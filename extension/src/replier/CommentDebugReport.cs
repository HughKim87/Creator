using System;using System.Linq;using System.Text;
namespace ReplierDesktop {
 public static class CommentDebugReport {
  static string Score(int? value){return value.HasValue ? value.Value.ToString() : "미평가";}
  static void Comment(StringBuilder text,CommentSuggestion c){
   if(!string.IsNullOrEmpty(c.FitError))text.AppendLine("후보별 평가 오류: "+c.FitError);
   if(c.SurfaceReviewed)text.AppendLine("말투 다듬기 전: "+c.DraftText);
   text.AppendLine(c.Text);text.AppendLine("적합도: "+Score(c.FitScore)+" / 100 · Gemma "+Score(c.GemmaFitScore)+" / 50 · Qwen "+Score(c.QwenFitScore)+" / 50");
   if(c.TiePreference>0)text.AppendLine("동점 최종 비교: "+c.TieReason);
   text.AppendLine("품질 판정: "+(c.FitEligible==true ? "통과" : c.FitEligible==false ? "제외 또는 미검증" : "미확인"));
   text.AppendLine("참고 시각: "+CaptionService.Timestamp(c.StartMs));text.AppendLine((SceneMaterial.IsScene(c.Material)?"상황 이해에 사용한 원문 구간: ":"선택한 원문 구절: ")+(c.GroundingQuote ?? "없음"));
   text.AppendLine("앞뒤 자막: "+(c.Evidence ?? "없음"));text.AppendLine("모델별 판단:\n"+(string.IsNullOrEmpty(c.FitReason)?"아직 평가되지 않았습니다.":c.FitReason));
  }
  public static string Format(Video video,DualCommentResult result,CommentSuggestion shown,string status,string error,string evidence=null){
   var text=new StringBuilder();text.AppendLine("24HReplier 댓글 디버깅 정보");text.AppendLine("복사 시각: "+DateTimeOffset.Now.ToString("yyyy-MM-dd HH:mm:ss zzz"));
   text.AppendLine("영상 제목: "+video.Title);text.AppendLine("영상 링크: "+video.Url);text.AppendLine("영상 채널: "+(video.Channel ?? "미확인"));text.AppendLine("화면 상태: "+status);
   if(!string.IsNullOrEmpty(error))text.AppendLine("생성 오류: "+error);
   if(!string.IsNullOrEmpty(evidence)){text.AppendLine();text.AppendLine("[생성에 사용한 자막 발췌]");text.AppendLine(evidence);}
   text.AppendLine();text.AppendLine("[화면에 표시된 최종 추천 댓글]");
   if(shown==null)text.AppendLine("없음 (미완료·실패 또는 전체 후보 제외)");else{if(result==null || !result.Batches.Any(b=>b.Result!=null && b.Result.Comments.Any(c=>object.ReferenceEquals(c,shown))))text.AppendLine("이전 결과 유지: 아래 최신 생성 결과와 별도입니다.");Comment(text,shown);}
   text.AppendLine();text.AppendLine("[최신 생성 결과 · 전체 후보]");
   if(result==null){text.AppendLine("생성 결과 없음");return text.ToString();}
   text.AppendLine("완료: "+result.Complete+" · 취소: "+result.Cancelled+" · 후보 수: "+result.Count);if(!string.IsNullOrEmpty(result.ScoreError))text.AppendLine("평가 오류: "+result.ScoreError);
   foreach(var batch in result.Batches){text.AppendLine();text.AppendLine("생성 모델: "+batch.Label+" ("+batch.Model+")");if(!string.IsNullOrEmpty(batch.Error))text.AppendLine("모델 오류: "+batch.Error);if(batch.Result==null){text.AppendLine("후보 없음");continue;}if(!string.IsNullOrEmpty(batch.Result.ReferenceStatus)){text.AppendLine("[기존 댓글 참고]");text.AppendLine(batch.Result.ReferenceStatus);text.AppendLine("반응 소재: "+batch.Result.ReactionGuide);if(batch.Result.ReferenceComments!=null)for(int n=0;n<batch.Result.ReferenceComments.Length;n++)text.AppendLine("참고 "+(n+1)+": "+batch.Result.ReferenceComments[n]);}if(!string.IsNullOrEmpty(batch.Result.ContextSummary)){text.AppendLine("[작성 전 상황 이해]");text.AppendLine(batch.Result.ContextSummary);}if(batch.Result.DraftNotes!=null && batch.Result.DraftNotes.Count>0){text.AppendLine("[작성 중 피드백]");foreach(string note in batch.Result.DraftNotes)text.AppendLine(note);}
   for(int i=0;i<batch.Result.Comments.Count;i++){text.AppendLine();text.AppendLine("후보 "+(i+1));Comment(text,batch.Result.Comments[i]);}}
   return text.ToString();
  }
 }
}
