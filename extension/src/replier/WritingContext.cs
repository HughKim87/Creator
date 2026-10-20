using System;using System.IO;using System.Linq;using System.Collections.Generic;using System.Web.Script.Serialization;
namespace ReplierDesktop {
 public sealed class WritingSource {
  public string Cue {get;set;}
  public string Fact {get;set;}
  public string Quote {get;set;}
  public long StartMs {get;set;}
 }
 // This is the evidence actually supplied to the writer, not a fresh video interpretation.
 public static class WritingContext {
  public static WritingSource[] Capture(Dictionary<string,CaptionCue> evidence,Dictionary<string,string> materials){
   return materials.Select(e=>{
    var material=SceneMaterial.Json(e.Value);var cue=evidence[e.Key];
    string quote=CaptionService.Get(material,"writing_quote") as string??cue.Text;
    return new WritingSource{Cue=e.Key,Fact=CommentPipeline.WritingQuote(CaptionService.Get(material,"writing_fact") as string??quote,e.Value),Quote=quote,StartMs=cue.StartMs};
   }).ToArray();
  }
  public static object[] Request(WritingSource[] sources){return sources.Select(s=>(object)new{cue=s.Cue,text=s.Fact}).ToArray();}
  public static string Store(string material,WritingSource[] sources){
   var root=(Dictionary<string,object>)SceneMaterial.Json(material);
   root["writing_context_version"]=1;root["writing_context"]=sources;
   return new JavaScriptSerializer().Serialize(root);
  }
  public static WritingSource[] Read(string material){
   if(!SceneMaterial.IsScene(material))return null;
   var root=SceneMaterial.Json(material);var version=CaptionService.Get(root,"writing_context_version");
   if(version==null)return null; // Existing candidates retain their original single-fact boundary.
   if(!object.Equals(version,1))throw new InvalidDataException("작성 근거 버전을 확인하지 못했습니다.");
   var json=new JavaScriptSerializer();var sources=json.Deserialize<WritingSource[]>(json.Serialize(CaptionService.Get(root,"writing_context")));
   if(sources==null||sources.Length==0||sources.Any(s=>s==null||string.IsNullOrWhiteSpace(s.Cue)||string.IsNullOrWhiteSpace(s.Fact)||string.IsNullOrWhiteSpace(s.Quote)))throw new InvalidDataException("작성 당시 제공한 근거를 확인하지 못했습니다.");
   return sources;
  }
  public static KeyValuePair<string,CaptionCue>[] Evidence(WritingSource[] sources){return ContextGuidance.Units(sources.Select(s=>new KeyValuePair<string,CaptionCue>(s.Cue,new CaptionCue{Text=s.Quote,StartMs=s.StartMs})).ToArray());}
 }
}
