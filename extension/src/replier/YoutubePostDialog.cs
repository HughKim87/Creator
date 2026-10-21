using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace ReplierDesktop
{
    public sealed class YoutubePostDialog : Form
    {
        readonly IYoutubePublisher publisher;
        readonly string videoId;
        readonly TextBox editor=new TextBox();
        readonly Label account=new Label(),status=new Label();
        readonly LinkLabel postedLink=new LinkLabel();
        readonly Button connect=new Button(),restore=new Button(),disconnect=new Button(),publish=new Button(),close=new Button();
        readonly CancellationTokenSource lifetime=new CancellationTokenSource();
        readonly Func<string> pickFile;
        bool working,sending,terminal;
        public Task OperationTask {get;private set;}
        public YoutubePostDialog(Video video,string text,IYoutubePublisher service,Func<string> filePicker=null)
        {
            if(video==null || !VideoSearch.ValidId(video.Id))throw new ArgumentException("영상을 먼저 선택해 주세요.");
            publisher=service;videoId=video.Id;pickFile=filePicker ?? PickFile;OperationTask=Task.FromResult(0);
            Text="유튜브 댓글 게시";Font=new Font("맑은 고딕",10);ClientSize=new Size(650,440);MinimumSize=new Size(480,360);
            StartPosition=FormStartPosition.CenterParent;ShowInTaskbar=false;MinimizeBox=false;MaximizeBox=false;
            var panel=new TableLayoutPanel{Dock=DockStyle.Fill,Padding=new Padding(16),ColumnCount=1,RowCount=7};
            panel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
            foreach(int h in new[]{48,30,40,0,60,48,34})panel.RowStyles.Add(h==0 ? new RowStyle(SizeType.Percent,100) : new RowStyle(SizeType.Absolute,h));
            Controls.Add(panel);
            var target=new Label{Name="PostTarget",Text=video.Title+"\n"+video.Url,AutoEllipsis=true,Dock=DockStyle.Fill};
            panel.Controls.Add(target,0,0);
            account.Name="PostingAccount";account.Dock=DockStyle.Fill;account.AutoEllipsis=true;panel.Controls.Add(account,0,1);
            var connections=new FlowLayoutPanel{Dock=DockStyle.Fill,WrapContents=false,AutoScroll=true};
            connect.Name="ConnectYoutube";connect.Text="OAuth 파일로 연결";connect.AutoSize=true;
            restore.Name="RestoreYoutube";restore.Text="저장된 연결 사용";restore.AutoSize=true;
            disconnect.Name="DisconnectYoutube";disconnect.Text="연결 해제";disconnect.AutoSize=true;
            connections.Controls.AddRange(new Control[]{connect,restore,disconnect});panel.Controls.Add(connections,0,2);
            editor.Name="PostText";editor.Multiline=true;editor.ScrollBars=ScrollBars.Vertical;editor.Dock=DockStyle.Fill;editor.MaxLength=1000;editor.Text=text;
            panel.Controls.Add(editor,0,3);
            status.Name="PostStatus";status.Dock=DockStyle.Fill;status.AutoEllipsis=true;panel.Controls.Add(status,0,4);
            var actions=new FlowLayoutPanel{Dock=DockStyle.Fill,FlowDirection=FlowDirection.RightToLeft,WrapContents=false};
            publish.Name="PublishYoutube";publish.Text="게시";publish.Width=100;publish.Height=36;
            close.Name="ClosePosting";close.Text="닫기";close.Width=80;close.Height=36;
            postedLink.Name="PostedCommentLink";postedLink.Text="유튜브에서 확인";postedLink.AutoSize=true;postedLink.Visible=false;postedLink.Margin=new Padding(6,10,6,0);
            actions.Controls.AddRange(new Control[]{publish,close,postedLink});panel.Controls.Add(actions,0,5);
            var help=new LinkLabel{Text="처음 연결하는 방법",AutoSize=true};panel.Controls.Add(help,0,6);
            help.LinkClicked+=(sender,e)=>ShowSetupHelp(this);
            connect.Click+=(sender,e)=>{
                string file=pickFile();if(file!=null)OperationTask=Connect(file);
            };
            restore.Click+=(sender,e)=>{OperationTask=Restore();};
            disconnect.Click+=(sender,e)=>{try{publisher.Disconnect();status.Text="이 앱에 저장된 연결을 해제했습니다.";}catch{status.Text="연결 정보를 지우지 못했습니다.";}UpdateControls();};
            publish.Click+=(sender,e)=>{OperationTask=Publish();};
            editor.TextChanged+=(sender,e)=>UpdateControls();
            close.Click+=(sender,e)=>{if(!sending)Close();};
            FormClosing+=(sender,e)=>{if(sending){e.Cancel=true;status.Text="댓글 전송 중입니다. 결과를 기다려 주세요.";}else lifetime.Cancel();};
            FormClosed+=(sender,e)=>lifetime.Cancel();
            Shown+=(sender,e)=>{
                var area=Screen.FromControl(this).WorkingArea;
                Size=new Size(Math.Min(Width,area.Width-16),Math.Min(Height,area.Height-16));
                Left=Math.Max(area.Left,Math.Min(Left,area.Right-Width));Top=Math.Max(area.Top,Math.Min(Top,area.Bottom-Height));
            };
            UpdateControls();
        }
        string PickFile()
        {
            using(var picker=new OpenFileDialog{Title="Google 데스크톱 앱 OAuth JSON 선택",Filter="OAuth JSON (*.json)|*.json",CheckFileExists=true})
                return picker.ShowDialog(this)==DialogResult.OK ? picker.FileName : null;
        }
        void UpdateControls()
        {
            if(IsDisposed)return;
            account.Text=publisher.Account==null ? "작성 채널 · 연결 필요" : "작성 채널 · "+publisher.Account.Title+" ("+publisher.Account.Id+")";
            connect.Enabled=restore.Enabled=!working && !terminal;
            disconnect.Enabled=!working && publisher.Account!=null && !terminal;
            editor.ReadOnly=working || terminal;
            publish.Enabled=!working && !terminal && publisher.Account!=null && !string.IsNullOrWhiteSpace(editor.Text);
            close.Enabled=!sending;close.Text=working ? "취소" : "닫기";
        }
        async Task Connect(string file){await Connection(()=>publisher.Connect(file,lifetime.Token));}
        async Task Restore(){await Connection(()=>publisher.Restore(lifetime.Token));}
        async Task Connection(Func<Task> action)
        {
            if(working || terminal)return;working=true;status.Text="계정 연결 중…";UpdateControls();
            try{await action();if(!IsDisposed)status.Text="작성 채널을 확인한 뒤 게시해 주세요.";}
            catch(Exception ex){if(!IsDisposed)status.Text=SafeError(ex,"계정을 연결하지 못했습니다. 설정을 확인해 주세요.");}
            finally{working=false;if(!IsDisposed)UpdateControls();}
        }
        async Task Publish()
        {
            if(working || terminal || publisher.Account==null || string.IsNullOrWhiteSpace(editor.Text))return;
            string text=editor.Text.Trim(),authorId=publisher.Account.Id;
            working=sending=true;status.Text="댓글 게시 중…";UpdateControls();
            try
            {
                var result=await publisher.Publish(videoId,text,authorId,lifetime.Token);
                terminal=true;status.Text="댓글이 등록되었습니다.";
                postedLink.LinkClicked+=(sender,e)=>Process.Start(new ProcessStartInfo(result.Url){UseShellExecute=true});
                postedLink.Visible=true;
            }
            catch(PostingUncertainException ex){terminal=true;status.Text=ex.Message;}
            catch(Exception ex){status.Text=SafeError(ex,"댓글을 게시하지 못했습니다. 인터넷 연결을 확인해 주세요.");}
            finally{sending=working=false;if(!IsDisposed)UpdateControls();}
        }
        static string SafeError(Exception ex,string fallback)
        {
            // Only messages created by this module can reach the UI, never HTTP/raw credential exceptions.
            return ex is InvalidOperationException || ex is ArgumentException ? ex.Message : fallback;
        }
        public static void ShowSetupHelp(IWin32Window owner)
        {
            using(var help=new Form{Text="유튜브 계정 연결 준비",Font=new Font("맑은 고딕",10),ClientSize=new Size(620,330),StartPosition=FormStartPosition.CenterParent,MinimizeBox=false,MaximizeBox=false})
            {
                var text=new TextBox{Multiline=true,ReadOnly=true,Dock=DockStyle.Fill,ScrollBars=ScrollBars.Vertical,Text=
                    "1. Google Cloud 프로젝트에서 YouTube Data API v3를 활성화합니다.\r\n\r\n"+
                    "2. Google Auth Platform에서 동의 화면을 설정합니다. 테스트 상태라면 로그인할 Google 계정을 테스트 사용자에 추가합니다.\r\n\r\n"+
                    "3. OAuth 클라이언트를 '데스크톱 앱'으로 생성하고 JSON 파일을 내려받습니다.\r\n\r\n"+
                    "4. 이 앱의 'OAuth 파일로 연결'에서 파일을 선택하고 기본 브라우저에서 로그인·권한 동의를 합니다.\r\n\r\n"+
                    "5. 앱에 표시된 작성 채널을 확인합니다. 다음 실행부터 저장된 계정으로 자동 연결됩니다.\r\n\r\n"+
                    "연결 정보는 이 Windows 사용자 전용으로 암호화해 저장됩니다. '연결 해제'는 앱의 저장 정보만 지웁니다. Google 계정의 앱 접근 권한은 계정 설정에서 해제할 수 있습니다."};
                var links=new FlowLayoutPanel{Dock=DockStyle.Bottom,Height=36};
                foreach(var entry in new[]{new[]{"Google Cloud 설정","https://console.cloud.google.com/auth/clients"},new[]{"공식 연결 안내","https://developers.google.com/identity/protocols/oauth2/native-app"}})
                {var url=entry[1];var link=new LinkLabel{Text=entry[0],AutoSize=true,Margin=new Padding(8)};link.LinkClicked+=(sender,e)=>Process.Start(new ProcessStartInfo(url){UseShellExecute=true});links.Controls.Add(link);}
                help.Controls.Add(text);help.Controls.Add(links);help.ShowDialog(owner);
            }
        }
    }
}
