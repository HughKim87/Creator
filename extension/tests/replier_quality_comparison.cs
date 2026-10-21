using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Threading;
using System.Web.Script.Serialization;
using ReplierDesktop;
public static class QualityComparison
{
 public static int Main(string[] args)
 {
  try{
   ServicePointManager.SecurityProtocol=SecurityProtocolType.Tls12;
   string extension=Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"..",".."));
   string name=args[0];
   var store=new ContentStore(Path.Combine(extension,"data","replier","content"));
   var videos=new[]{new Video{Id="HPUpsEzL1ps",Title="스팀평가 매우긍정적 이상! 꿀잼 인디게임 추천 14종"},
    new Video{Id="gx4mlQJHtJY",Title="내 목소리를 감지해서 쫓아오는 로블록스 공포 게임"}};
   var records=new List<object>();
   using(var model=new LocalModel(Path.Combine(extension,".runtime","replier-llm"),name))
   {
    var service=new CommentService(model);
    foreach(var video in videos)
    {
     var content=store.Load(video.Id);
     if(content==null){try{content=CaptionService.Fetch(video,CancellationToken.None).GetAwaiter().GetResult();}catch(ContentUnavailable){Console.WriteLine("SKIP unavailable captions "+video.Id);continue;}}
     var started=DateTime.UtcNow;
     var result=service.Generate(video,content,CancellationToken.None).GetAwaiter().GetResult();
     double elapsed=(DateTime.UtcNow-started).TotalSeconds;
     Console.WriteLine("MODEL "+name+" VIDEO "+video.Id+" SECONDS "+elapsed.ToString("F1"));
     foreach(var item in result.Comments)Console.WriteLine("COMMENT "+item.Text);
     records.Add(new{model=name,video=video.Id,title=video.Title,seconds=elapsed,comments=result.Comments.Select(c=>c.Text).ToArray()});
    }
   }
   string output=Path.Combine(extension,"data","replier-comment-checks","comparison-"+name.Replace(':','-')+".json");
   File.WriteAllText(output,new JavaScriptSerializer().Serialize(records));
   if(records.Count==0)throw new Exception("No actual video captions were available");
   return 0;
  }catch(Exception ex){Console.Error.WriteLine(ex.GetType().Name+": "+ex.Message);return 1;}
 }
}