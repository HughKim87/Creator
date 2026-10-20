using System;using System.Text.RegularExpressions;
namespace ReplierDesktop {
 public static class ViewerQuality {
  public static string SourceProblem(string text,string quote){
   string comment=Regex.Replace(text??"",@"[^가-힣A-Za-z0-9]","");string source=Regex.Replace(quote??"",@"[^가-힣A-Za-z0-9]","");
   if(comment.Length>=6 && source.Contains(comment))return "자기 반응 없이 영상 대사를 그대로 반복";
   return null;
  }
  public static string Problem(string text){
   if(Regex.IsMatch(text??"",@"^\s*그게(?:\s|[,，])"))return "앞 문장 없이 그게로 시작하여 대상이 불분명함";
   if(Regex.IsMatch(text??"",@"(?:분들|분은).{0,30}(?:도움|구매|구입)|구매하시면"))return "시청자 반응 대신 타인에게 구매·효용을 안내하는 말투";
   string clean=Regex.Replace(text??"",@"[\p{P}ㅋㅎ]","");
   foreach(Match phrase in Regex.Matches(clean,@"[가-힣]{1,5}\s+[가-힣]{1,5}")){
    string value=Regex.Replace(phrase.Value,@"(?:면|는|은|도|가|이|을|를)$","");
    if(value.Length>=4 && Regex.Matches(clean,Regex.Escape(value)).Count>=2)return "같은 구절을 불필요하게 반복";
   }
   return null;
  }
 }
}
