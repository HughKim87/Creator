using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Web;
using System.Web.Script.Serialization;

namespace ReplierDesktop
{
    public sealed class YoutubeAccount
    {
        public string Id, Title;
    }
    public sealed class PostedComment
    {
        public string Id, VideoId;
        public string Url { get { return "https://www.youtube.com/watch?v="+VideoId+"&lc="+Uri.EscapeDataString(Id); } }
    }
    public sealed class PostingUncertainException : InvalidOperationException
    {
        public PostingUncertainException() : base("게시 결과를 확인하지 못했습니다. 유튜브에서 확인해 주세요. 중복 방지를 위해 재전송하지 않습니다.") { }
    }
    public interface IYoutubePublisher
    {
        YoutubeAccount Account { get; }
        Task Connect(string clientFile, CancellationToken token);
        Task Restore(CancellationToken token);
        void Disconnect();
        Task<PostedComment> Publish(string videoId, string text, string authorChannelId, CancellationToken token);
    }
    // Never serialize credentials into project data, diagnostics or exception messages.
    public sealed class MissingYoutubeConnectionException : InvalidOperationException
    {
        public MissingYoutubeConnectionException() : base("저장된 연결이 없습니다. 먼저 계정을 연결해 주세요.") { }
    }
    public sealed class YoutubeCredentials
    {
        public string ClientId {get;set;}
        public string ClientSecret {get;set;}
        public string RefreshToken {get;set;}
    }
    public interface IYoutubeCredentialStore
    {
        YoutubeCredentials Load();
        void Save(YoutubeCredentials value);
    }
    public sealed class EncryptedYoutubeCredentialStore : IYoutubeCredentialStore
    {
        readonly string path;
        static readonly byte[] entropy=Encoding.UTF8.GetBytes("24HReplier.YouTube.OAuth.v1");
        public EncryptedYoutubeCredentialStore(string file){path=file;}
        public YoutubeCredentials Load()
        {
            if(!File.Exists(path))return null;
            byte[] plain=null;
            try
            {
                plain=ProtectedData.Unprotect(File.ReadAllBytes(path),entropy,DataProtectionScope.CurrentUser);
                return new JavaScriptSerializer().Deserialize<YoutubeCredentials>(Encoding.UTF8.GetString(plain));
            }
            catch{throw new InvalidOperationException("저장된 연결을 읽지 못했습니다. OAuth 파일로 다시 연결해 주세요.");}
            finally{if(plain!=null)Array.Clear(plain,0,plain.Length);}
        }
        public void Save(YoutubeCredentials value)
        {
            byte[] plain=Encoding.UTF8.GetBytes(new JavaScriptSerializer().Serialize(value));
            try
            {
                var encrypted=ProtectedData.Protect(plain,entropy,DataProtectionScope.CurrentUser);
                Directory.CreateDirectory(Path.GetDirectoryName(path));
                string temp=path+".new";
                File.WriteAllBytes(temp,encrypted);
                if(File.Exists(path))File.Replace(temp,path,null);else File.Move(temp,path);
            }
            catch{throw new InvalidOperationException("연결 정보를 암호화해 저장하지 못했습니다.");}
            finally{Array.Clear(plain,0,plain.Length);}
        }
    }
    public static class YoutubeOAuth
    {
        public const string Scope="https://www.googleapis.com/auth/youtube.force-ssl";
        public static string RandomValue()
        {
            var bytes=new byte[32];using(var rng=RandomNumberGenerator.Create())rng.GetBytes(bytes);
            return Base64Url(bytes);
        }
        static string Base64Url(byte[] bytes){return Convert.ToBase64String(bytes).TrimEnd('=').Replace('+','-').Replace('/','_');}
        public static string Challenge(string verifier){using(var hash=SHA256.Create())return Base64Url(hash.ComputeHash(Encoding.ASCII.GetBytes(verifier)));}
        public static YoutubeCredentials ParseClient(string json)
        {
            try
            {
                var installed=CaptionService.Get(new JavaScriptSerializer().DeserializeObject(json),"installed");
                string id=CaptionService.Get(installed,"client_id") as string;
                string secret=CaptionService.Get(installed,"client_secret") as string;
                if(string.IsNullOrEmpty(id) || !id.EndsWith(".apps.googleusercontent.com",StringComparison.Ordinal) || id.Any(char.IsControl))throw new Exception();
                return new YoutubeCredentials{ClientId=id,ClientSecret=secret,RefreshToken=""};
            }
            catch{throw new InvalidOperationException("Google의 데스크톱 앱용 OAuth JSON 파일을 선택해 주세요.");}
        }
        public static string AuthorizationUrl(string clientId,string redirect,string state,string verifier)
        {
            return "https://accounts.google.com/o/oauth2/v2/auth?"+Form(new Dictionary<string,string>{
                {"client_id",clientId},{"redirect_uri",redirect},{"response_type","code"},{"scope",Scope},
                {"state",state},{"code_challenge",Challenge(verifier)},{"code_challenge_method","S256"},
                {"access_type","offline"},{"prompt","consent select_account"}});
        }
        internal static string Form(IDictionary<string,string> values)
        {return string.Join("&",values.Select(kv=>Uri.EscapeDataString(kv.Key)+"="+Uri.EscapeDataString(kv.Value ?? "")));}
        public static string ValidateCallback(string target,string state)
        {
            if(!target.StartsWith("/callback?",StringComparison.Ordinal))throw new InvalidOperationException("로그인 응답 경로가 일치하지 않습니다.");
            var query=HttpUtility.ParseQueryString(target.Substring(target.IndexOf('?')+1));
            if(query["state"]!=state)throw new InvalidOperationException("로그인 응답을 확인하지 못했습니다. 다시 연결해 주세요.");
            if(!string.IsNullOrEmpty(query["error"]))throw new InvalidOperationException("계정 연결이 취소되었거나 허용되지 않았습니다.");
            if(string.IsNullOrEmpty(query["code"]) || query["code"].Contains(","))throw new InvalidOperationException("로그인 코드를 받지 못했습니다.");
            return query["code"];
        }
        public static Task<string> Authorize(string clientId,CancellationToken token)
        {
            return AuthorizeWithBrowser(clientId,token,url=>Process.Start(new ProcessStartInfo(url){UseShellExecute=true}));
        }
        public static async Task<string> AuthorizeWithBrowser(string clientId,CancellationToken token,Action<string> openBrowser)
        {
            using(var timeout=CancellationTokenSource.CreateLinkedTokenSource(token))
            {
                timeout.CancelAfter(TimeSpan.FromMinutes(3));
                var listener=new TcpListener(IPAddress.Loopback,0);listener.Start();
                try
                {
                    int port=((IPEndPoint)listener.LocalEndpoint).Port;
                    string redirect="http://127.0.0.1:"+port+"/callback";
                    string state=RandomValue(),verifier=RandomValue();
                    using(timeout.Token.Register(()=>listener.Stop()))
                    {
                        openBrowser(AuthorizationUrl(clientId,redirect,state,verifier));
                        while(true)
                        {
                            using(var connection=await listener.AcceptTcpClientAsync().ConfigureAwait(false))
                            using(var stream=connection.GetStream())
                            {
                                var buffer=new byte[8192];int size=0;
                                using(var requestTimeout=CancellationTokenSource.CreateLinkedTokenSource(timeout.Token))
                                {
                                    requestTimeout.CancelAfter(TimeSpan.FromSeconds(5));
                                    while(size<buffer.Length)
                                    {
                                        int read=await stream.ReadAsync(buffer,size,buffer.Length-size,requestTimeout.Token).ConfigureAwait(false);
                                        if(read==0)break;size+=read;
                                        if(Encoding.ASCII.GetString(buffer,0,size).Contains("\r\n\r\n"))break;
                                    }
                                }
                                string request=Encoding.ASCII.GetString(buffer,0,size);
                                string line=request.Split(new[]{"\r\n"},StringSplitOptions.None)[0];
                                string[] parts=line.Split(' ');
                                string code=null;
                                bool invalid=false,denied=false;
                                try
                                {
                                    if(parts.Length!=3 || parts[0]!="GET" || !request.Contains("\r\nHost: 127.0.0.1:"+port+"\r\n"))throw new InvalidOperationException();
                                    code=ValidateCallback(parts[1],state);
                                }
                                catch(InvalidOperationException)
                                {
                                    invalid=true;
                                    denied=parts.Length==3 && parts[1].StartsWith("/callback?") && HttpUtility.ParseQueryString(parts[1].Substring(10))["state"]==state;
                                }
                                if(invalid)
                                {
                                    var bad=Encoding.ASCII.GetBytes("HTTP/1.1 400 Bad Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n");
                                    await stream.WriteAsync(bad,0,bad.Length,timeout.Token).ConfigureAwait(false);
                                    if(denied)throw new InvalidOperationException("계정 연결이 취소되었거나 허용되지 않았습니다.");
                                    continue;
                                }
                                string html="<html><meta charset='utf-8'><body>24HReplier 연결 확인 중입니다. 앱으로 돌아가 주세요.</body></html>";
                                byte[] body=Encoding.UTF8.GetBytes(html);
                                byte[] head=Encoding.ASCII.GetBytes("HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\nConnection: close\r\nContent-Length: "+body.Length+"\r\n\r\n");
                                await stream.WriteAsync(head,0,head.Length,timeout.Token).ConfigureAwait(false);
                                await stream.WriteAsync(body,0,body.Length,timeout.Token).ConfigureAwait(false);
                                // Only consumed in memory by the token exchange; never shown or persisted.
                                return new JavaScriptSerializer().Serialize(new[]{code,redirect,verifier});
                            }
                        }
                    }
                }
                catch(OperationCanceledException){throw new InvalidOperationException(token.IsCancellationRequested ? "계정 연결을 취소했습니다." : "계정 연결 시간이 초과되었습니다.");}
                catch(SocketException){throw new InvalidOperationException("계정 연결이 취소되었거나 로그인 수신에 실패했습니다.");}
                catch(ObjectDisposedException){throw new InvalidOperationException("계정 연결을 취소했습니다.");}
                finally{listener.Stop();}
            }
        }
    }
    public sealed class YoutubePublisher : IYoutubePublisher, IDisposable
    {
        readonly HttpClient client;
        readonly IYoutubeCredentialStore store;
        readonly Func<string,CancellationToken,Task<string>> authorize;
        readonly SemaphoreSlim gate=new SemaphoreSlim(1,1);
        YoutubeCredentials credentials;
        string accessToken;
        DateTime expires;
        public YoutubeAccount Account {get;private set;}
        public YoutubePublisher(IYoutubeCredentialStore storage,HttpMessageHandler handler=null,Func<string,CancellationToken,Task<string>> authorizer=null)
        {
            store=storage;authorize=authorizer ?? YoutubeOAuth.Authorize;
            client=handler==null ? new HttpClient(new HttpClientHandler{AllowAutoRedirect=false}) : new HttpClient(handler);
            client.Timeout=TimeSpan.FromSeconds(35);
        }
        static string Field(object value,string key){return CaptionService.Get(value,key) as string ?? "";}
        static object Parse(string text){try{return new JavaScriptSerializer().DeserializeObject(text);}catch{throw new InvalidOperationException("YouTube 응답을 읽지 못했습니다.");}}
        static InvalidOperationException ApiError(string text,bool auth)
        {
            if(auth)return new InvalidOperationException("로그인이 만료되었거나 권한이 없습니다. 계정을 다시 연결해 주세요.");
            object parsed=null;try{parsed=Parse(text);}catch{}
            string reason="";var errors=CaptionService.Get(CaptionService.Get(parsed,"error"),"errors") as object[];
            if(errors!=null && errors.Length>0)reason=Field(errors[0],"reason");
            string message=reason=="commentsDisabled" ? "댓글이 사용 중지된 영상입니다." :
                reason=="quotaExceeded" || reason=="dailyLimitExceeded" ? "YouTube API 일일 할당량을 초과했습니다." :
                reason=="accessNotConfigured" ? "Google 프로젝트에서 YouTube Data API v3를 활성화해 주세요." :
                reason=="videoNotFound" ? "영상을 찾을 수 없거나 접근할 수 없습니다." :
                reason=="ineligibleAccount" || reason=="youtubeSignupRequired" ? "댓글을 작성할 YouTube 채널이 있는 계정으로 연결해 주세요." :
                "YouTube가 요청을 거부했습니다. 계정 권한과 영상의 댓글 설정을 확인해 주세요.";
            return new InvalidOperationException(message);
        }
        async Task<string> Read(HttpResponseMessage response)
        {
            await response.Content.LoadIntoBufferAsync(1048576).ConfigureAwait(false);
            return await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        }
        async Task Token(IDictionary<string,string> values,CancellationToken token)
        {
            values["client_id"]=credentials.ClientId;
            if(!string.IsNullOrEmpty(credentials.ClientSecret))values["client_secret"]=credentials.ClientSecret;
            using(var response=await client.PostAsync("https://oauth2.googleapis.com/token",new FormUrlEncodedContent(values),token).ConfigureAwait(false))
            {
                string text=await Read(response).ConfigureAwait(false);
                if(!response.IsSuccessStatusCode)throw ApiError("",true);
                var data=Parse(text);string access=Field(data,"access_token"),scope=Field(data,"scope");
                int seconds;
                if(access.Length==0 || !int.TryParse(Convert.ToString(CaptionService.Get(data,"expires_in")),out seconds) || seconds<=0 ||
                    (scope.Length>0 && !scope.Split(' ').Contains(YoutubeOAuth.Scope)))throw ApiError("",true);
                string refresh=Field(data,"refresh_token");if(refresh.Length>0)credentials.RefreshToken=refresh;
                accessToken=access;expires=DateTime.UtcNow.AddSeconds(Math.Min(seconds,86400)-30);
            }
        }
        async Task EnsureToken(CancellationToken token)
        {
            if(credentials==null)throw new InvalidOperationException("먼저 유튜브 계정을 연결해 주세요.");
            if(!string.IsNullOrEmpty(accessToken) && expires>DateTime.UtcNow)return;
            if(string.IsNullOrEmpty(credentials.RefreshToken))throw ApiError("",true);
            await Token(new Dictionary<string,string>{{"grant_type","refresh_token"},{"refresh_token",credentials.RefreshToken}},token).ConfigureAwait(false);
            if(Account!=null)store.Save(credentials);
        }
        async Task<object> Get(string path,CancellationToken token)
        {
            await EnsureToken(token).ConfigureAwait(false);
            using(var request=new HttpRequestMessage(HttpMethod.Get,"https://www.googleapis.com/youtube/v3/"+path))
            {
                request.Headers.Authorization=new AuthenticationHeaderValue("Bearer",accessToken);
                using(var response=await client.SendAsync(request,token).ConfigureAwait(false))
                {
                    string text=await Read(response).ConfigureAwait(false);
                    if(!response.IsSuccessStatusCode)throw ApiError(text,response.StatusCode==HttpStatusCode.Unauthorized);
                    return Parse(text);
                }
            }
        }
        async Task<YoutubeAccount> FetchAccount(CancellationToken token)
        {
            var items=CaptionService.Get(await Get("channels?part=snippet&mine=true",token).ConfigureAwait(false),"items") as object[];
            if(items==null || items.Length!=1)throw new InvalidOperationException("작성할 YouTube 채널을 하나 선택해 다시 연결해 주세요.");
            string id=Field(items[0],"id"),title=Field(CaptionService.Get(items[0],"snippet"),"title");
            if(!System.Text.RegularExpressions.Regex.IsMatch(id,@"\AUC[A-Za-z0-9_-]{22}\z") || title.Length==0)throw new InvalidOperationException("작성 채널을 확인하지 못했습니다.");
            return new YoutubeAccount{Id=id,Title=title};
        }
        public async Task Connect(string clientFile,CancellationToken token)
        {
            await gate.WaitAsync(token).ConfigureAwait(false);
            try
            {
                Account=null;accessToken=null;
                if(new FileInfo(clientFile).Length>65536)throw new InvalidOperationException("OAuth 설정 파일이 너무 큽니다.");
                credentials=YoutubeOAuth.ParseClient(File.ReadAllText(clientFile,Encoding.UTF8));
                string[] reply=new JavaScriptSerializer().Deserialize<string[]>(await authorize(credentials.ClientId,token).ConfigureAwait(false));
                await Token(new Dictionary<string,string>{{"grant_type","authorization_code"},{"code",reply[0]},{"redirect_uri",reply[1]},{"code_verifier",reply[2]}},token).ConfigureAwait(false);
                var account=await FetchAccount(token).ConfigureAwait(false);
                if(string.IsNullOrEmpty(credentials.RefreshToken))throw new InvalidOperationException("연결 유지 권한을 받지 못했습니다. 다시 연결해 주세요.");
                token.ThrowIfCancellationRequested();store.Save(credentials);Account=account;
            }
            catch{Account=null;accessToken=null;credentials=null;throw;}
            finally{gate.Release();}
        }
        public async Task Restore(CancellationToken token)
        {
            await gate.WaitAsync(token).ConfigureAwait(false);
            try
            {
                Account=null;accessToken=null;credentials=store.Load();
                if(credentials==null)throw new MissingYoutubeConnectionException();
                var account=await FetchAccount(token).ConfigureAwait(false);token.ThrowIfCancellationRequested();store.Save(credentials);Account=account;
            }
            catch{Account=null;accessToken=null;credentials=null;throw;}
            finally{gate.Release();}
        }
        public void Disconnect(){Account=null;accessToken=null;credentials=null;store.Save(null);}
        public async Task<PostedComment> Publish(string videoId,string text,string authorChannelId,CancellationToken token)
        {
            if(!VideoSearch.ValidId(videoId))throw new ArgumentException("게시할 영상 ID가 올바르지 않습니다.");
            text=(text ?? "").Trim();
            if(text.Length==0 || text.Length>1000)throw new ArgumentException("댓글은 1~1,000자로 입력해 주세요.");
            if(!await gate.WaitAsync(0,token).ConfigureAwait(false))throw new InvalidOperationException("이미 계정 연결 또는 게시를 처리 중입니다.");
            try
            {
                if(Account==null || Account.Id!=authorChannelId)throw new InvalidOperationException("작성 계정이 바뀌었습니다. 계정을 확인한 뒤 게시 창을 다시 열어 주세요.");
                var verified=await FetchAccount(token).ConfigureAwait(false);
                if(verified.Id!=authorChannelId){Account=null;throw new InvalidOperationException("작성 계정이 바뀌었습니다. 다시 연결해 주세요.");}
                var items=CaptionService.Get(await Get("videos?part=snippet&id="+videoId,token).ConfigureAwait(false),"items") as object[];
                if(items==null || items.Length!=1 || Field(items[0],"id")!=videoId)throw new InvalidOperationException("게시할 영상을 확인하지 못했습니다.");
                string owner=Field(CaptionService.Get(items[0],"snippet"),"channelId");
                if(!System.Text.RegularExpressions.Regex.IsMatch(owner,@"\AUC[A-Za-z0-9_-]{22}\z"))throw new InvalidOperationException("영상 채널을 확인하지 못했습니다.");
                var body=new {snippet=new {channelId=owner,videoId=videoId,topLevelComment=new {snippet=new {textOriginal=text}}}};
                using(var request=new HttpRequestMessage(HttpMethod.Post,"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet"))
                {
                    request.Headers.Authorization=new AuthenticationHeaderValue("Bearer",accessToken);
                    request.Content=new StringContent(new JavaScriptSerializer().Serialize(body),Encoding.UTF8,"application/json");
                    token.ThrowIfCancellationRequested();
                    try
                    {
                        using(var response=await client.SendAsync(request,token).ConfigureAwait(false))
                        {
                            string responseText=await Read(response).ConfigureAwait(false);
                            if((int)response.StatusCode>=500 || response.StatusCode==HttpStatusCode.RequestTimeout)throw new PostingUncertainException();
                            if(!response.IsSuccessStatusCode)throw ApiError(responseText,response.StatusCode==HttpStatusCode.Unauthorized);
                            object data;try{data=Parse(responseText);}catch{throw new PostingUncertainException();}
                            var snippet=CaptionService.Get(data,"snippet");var comment=CaptionService.Get(snippet,"topLevelComment");
                            string id=Field(comment,"id");
                            if(id.Length==0 || Field(snippet,"videoId")!=videoId)throw new PostingUncertainException();
                            return new PostedComment{Id=id,VideoId=videoId};
                        }
                    }
                    catch(IOException){throw new PostingUncertainException();}
                    catch(HttpRequestException){throw new PostingUncertainException();}
                    catch(OperationCanceledException){throw new PostingUncertainException();}
                }
            }
            finally{gate.Release();}
        }
        public void Dispose(){client.Dispose();}
    }
}
