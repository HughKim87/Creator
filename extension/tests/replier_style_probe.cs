using System;using System.IO;using System.Linq;using System.Threading;using System.Web.Script.Serialization;using ReplierDesktop;
public static class StyleProbe{
public static int Main(){try{string extension=Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"..",".."));var s=new JavaScriptSerializer();var records=(object[])s.DeserializeObject(File.ReadAllText(Path.Combine(extension,"data","replier-natural-comment-checks","natural-comments.json")));
foreach(string name in new[]{"gemma4:e2b-it-qat","qwen3.5:4b"})using(var m=new LocalModel(Path.Combine(extension,".runtime","replier-llm"),name)){
var record=records.First(r=>(string)CaptionService.Get(r,"model")==name);var comments=(object[])CaptionService.Get(record,"comments");
foreach(var c in comments.Skip(2).Take(2)){
string text=(string)CaptionService.Get(c,"Text"),evidence=(string)CaptionService.Get(c,"Evidence");
string edited=m.Chat(new{model=m.Name,stream=false,think=false,keep_alive="30s",options=m.WriterOptions(true),messages=new[]{new{role="system",content="한국어 댓글 편집자다. 초안을 사람이 툭 남기는 짧은 존댓말로 고친다. 게임 설명·이름·숫자·특정 행동·몸 상태·과한 감탄은 모두 빼고, 소재와 어긋나지 않는 가벼운 반응 하나만 남긴다. 자료에 없는 사실이나 경험은 만들지 않는다. 말이 이상하면 초안을 버리고 새로 쓴다. 10~40자 정도 한 문장만 출력한다."},new{role="user",content="참고 자막: "+evidence+"\n초안: "+text+"\n짧고 편한 댓글로 고쳐줘. 해설 없이 댓글만."}}},CancellationToken.None).GetAwaiter().GetResult();Console.WriteLine(name+" BEFORE "+text+" AFTER "+edited);
}m.Unload().GetAwaiter().GetResult();}return 0;}catch(Exception e){Console.Error.WriteLine(e);return 1;}}}
