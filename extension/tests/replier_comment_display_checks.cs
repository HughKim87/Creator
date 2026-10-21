using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Windows.Forms;
using ReplierDesktop;
public static class CommentDisplayChecks
{
 static void Check(bool ok,string label){if(!ok)throw new Exception(label);Console.WriteLine("PASS "+label);}
 [STAThread] public static int Main(string[] args){try{
  Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
  string output=Path.GetFullPath(args[0]);Directory.CreateDirectory(output);
  using(var form=new MainForm(Path.Combine(output,"history.json"))){
   form.ShowInTaskbar=false;form.Opacity=0;form.Show();Application.DoEvents();
   var result=new DualCommentResult {Complete=true};int?[] scores={70,60,100,85,0,85,95,40,80,65};
   for(int m=0;m<2;m++)result.Batches.Add(new ModelCommentBatch {Model=m==0?"gemma4:e2b-it-qat":"qwen3.5:4b",Label=m==0?"Gemma":"Qwen",Result=new CommentResult{Comments=Enumerable.Range(m*5,5).Select(i=>new CommentSuggestion{Text="구경만 하려고 왔다가 시간 가는 줄 모르겠네요. 긴 댓글도 한 줄만 표시하고 마우스를 올리면 전체 내용을 확인합니다. "+i,Evidence="실제 자막이 아닌 UI 검사용 긴 참고 대사입니다. 창 너비가 줄어도 다른 줄로 넘어가지 않습니다. "+i,StartMs=i*1000,FitScore=scores[i],FitReason="합성 점수 표시 검사"}).ToList()}});
   typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{result});Application.DoEvents();
   var grid=(DataGridView)form.Controls.Find("Comments",true)[0];
   Check(grid.Rows.Count==1,"only highest scored comment is shown");
   result.ScoreError="적합도 평가 실패 · 평가한 댓글 원문이 일치하지 않습니다.";
   typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{result});
   Check(grid.Rows.Count==1 && grid.Rows[0].Cells["fit"].Value.ToString()=="미평가" && object.ReferenceEquals(grid.Rows[0].Tag,result.Batches[0].Result.Comments[0]),"grading failure presents generation-first provisional comment without reusing stale numeric scores");
   Check(grid.Columns["fit"].HeaderCell.SortGlyphDirection==SortOrder.None && grid.Rows[0].Cells["fit"].ToolTipText.Contains("생성 순서"),"ungraded provisional comment has no winner or sort claim");
   result.ScoreError="";typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{result});
   var bestItem=result.Batches[0].Result.Comments[2];var runnerItem=result.Batches[1].Result.Comments[1];
   bestItem.FitTopicScore=40;bestItem.FitToneScore=20;bestItem.FitCareScore=10;bestItem.FitLinkScore=30;
   runnerItem.FitTopicScore=37;runnerItem.FitToneScore=18;runnerItem.FitCareScore=10;runnerItem.FitLinkScore=30;
   typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{result});
   Check(grid.Rows[0].Cells["fit"].ToolTipText.Contains("주제 어울림 +3점") && grid.Rows[0].Cells["fit"].ToolTipText.Contains("말투 +2점") && grid.Rows[0].Cells["fit"].ToolTipText.Contains(runnerItem.Text),"selection explanation attributes score difference to measured criteria and identifies runner-up");
   Check(grid.Rows[0].Cells["fit"].ToolTipText.Contains("10개 후보") && grid.Rows[0].Cells["fit"].ToolTipText.Contains("차점 95점보다 5점"),"winner explanation shows comparison with runner-up");
   bool detailsOpened=false;
   using(var detailsTimer=new Timer{Interval=40}){
    detailsTimer.Tick+=(sender,e)=>{var d=Application.OpenForms.Cast<Form>().FirstOrDefault(x=>x.Text=="댓글 선정 이유와 적합도");if(d==null)return;detailsOpened=d.Controls.Find("FitDetails",true)[0].Text.Contains("차점 95점보다 5점");d.Close();detailsTimer.Stop();};
    detailsTimer.Start();typeof(MainForm).GetMethod("ShowFitDetails",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{grid.Rows[0]});
   }
   Check(detailsOpened,"score details open readable full selection explanation");
   var posting=(Button)form.Controls.Find("PostComment",true)[0];
   Check(!posting.Enabled,"posting needs an actual selected video");
   typeof(MainForm).GetField("currentVideo",BindingFlags.NonPublic|BindingFlags.Instance).SetValue(form,new Video{Id="V0000000001",Title="합성 영상"});
   typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{result});
   Check(posting.Enabled,"single scored winner enables posting review");
   bool opened=false;
   using(var timer=new Timer{Interval=40}){
    timer.Tick+=(sender,e)=>{
     var dialog=Application.OpenForms.Cast<Form>().FirstOrDefault(f=>f is YoutubePostDialog);
     if(dialog==null)return;
     opened=dialog.Controls.Find("PostTarget",true)[0].Text.Contains("V0000000001") && dialog.Controls.Find("PostText",true)[0].Text==result.Batches[0].Result.Comments[2].Text;
     dialog.Close();timer.Stop();
    };
    timer.Start();posting.PerformClick();
   }
   Check(opened,"posting button opens review for current video and winning comment without connecting or posting");
   var expected=new[]{2};
   Check(grid.Rows.Cast<DataGridViewRow>().Select(r=>r.Cells["text"].Value.ToString()).SequenceEqual(expected.Select(i=>result.Batches[i/5].Result.Comments[i%5].Text)),"numeric score descending including stable ties and unscored last");
   Check(grid.Rows.Cast<DataGridViewRow>().Select((r,index)=>r.Cells["model"].Value.ToString()==result.Batches[expected[index]/5].Label && r.Cells["evidence"].ToolTipText==result.Batches[expected[index]/5].Result.Comments[expected[index]%5].Evidence).All(x=>x),"model labels and reference tooltips follow the same ranked comment");
   Check(result.Batches[0].Result.Comments[0].FitScore==70,"render sorting does not reorder generation cache");
   Check(grid.AutoSizeRowsMode==DataGridViewAutoSizeRowsMode.None && grid.DefaultCellStyle.WrapMode==DataGridViewTriState.False && grid.Rows.Cast<DataGridViewRow>().Select(r=>r.Height).Distinct().Count()==1,"comments and references use fixed single-line rows");
   Check(grid.Rows.Cast<DataGridViewRow>().All(r=>r.Cells["text"].ToolTipText==r.Cells["text"].Value.ToString() && r.Cells["evidence"].ToolTipText.Length>24),"full long comments and reference text remain in tooltips");
   Check(grid.Columns["fit"].HeaderCell.SortGlyphDirection==SortOrder.Descending,"score header indicates descending order");
   form.Size=new Size(800,600);Application.DoEvents();
   Check(grid.Rows.Cast<DataGridViewRow>().Select(r=>r.Height).Distinct().Count()==1,"shrinking window does not wrap or expand rows");
   using(var bitmap=new Bitmap(form.Width,form.Height)){form.DrawToBitmap(bitmap,new Rectangle(Point.Empty,bitmap.Size));bitmap.Save(Path.Combine(output,"comment-display-preview.png"),ImageFormat.Png);}
   result.Batches[1].Result.Comments[1].FitScore=100;
   typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{result});
   Check(object.ReferenceEquals(grid.Rows[0].Tag,result.Batches[0].Result.Comments[2]),"equal scores keep original candidate order");
   Check(grid.Rows[0].Cells["fit"].ToolTipText.Contains("동점 2개") && grid.Rows[0].Cells["fit"].ToolTipText.Contains("먼저 생성"),"ties explain generation order rather than invent superiority");
   result.Batches[1].Result.Comments[1].FitScore=101;
   typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{result});
   Check(object.ReferenceEquals(grid.Rows[0].Tag,result.Batches[0].Result.Comments[2]),"invalid score cannot replace existing winner");
   result.Batches[1].Result.Comments[1].FitScore=99;
   result.Batches[0].Result.Comments[2].FitScore=null;
   grid.Rows.Clear();
   typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{result});
   Check(grid.Rows.Count==0,"incomplete grading does not publish a false winner");
   result.Batches[0].Result.Comments[2].FitScore=90;
   typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{result});
   Check(object.ReferenceEquals(grid.Rows[0].Tag,result.Batches[1].Result.Comments[1]),"winner can come from Qwen across both models");
   typeof(MainForm).GetMethod("ClearVideo",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[0]);
   Check(!posting.Enabled,"clearing video disables posting");
   result.Batches[0].Result.Comments=result.Batches[0].Result.Comments.Take(2).ToList();result.Batches[0].Result.QualityFiltered=true;
   result.Batches[1].Result.Comments.Clear();result.Batches[1].Result.QualityFiltered=true;
   grid.Rows.Clear();typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{result});
   Check(grid.Rows.Count==1 && grid.Rows[0].Cells["fit"].ToolTipText.Contains("2개 후보"),"only quality-passing candidates are ranked without filling ten slots");
   result.Batches[0].Result.QualityFiltered=false;grid.Rows.Clear();
   typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{result});
   Check(grid.Rows.Count==0,"unexplained short model result remains incomplete instead of bypassing failure handling");
   result.Batches[0].Result.QualityFiltered=true;
   var vetoed=result.Batches[0].Result.Comments[0];var accepted=result.Batches[0].Result.Comments[1];vetoed.FitScore=100;vetoed.FitEligible=false;accepted.FitScore=60;accepted.FitEligible=true;
   typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{result});
   Check(grid.Rows.Count==1 && object.ReferenceEquals(grid.Rows[0].Tag,accepted),"rejected high-score candidate cannot win over approved lower-score reaction");
   accepted.GroundingQuote="실제로 선택한\n자막 구절";accepted.Material="{\"avoid_names\":[\"내부정보\"]}";
   typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{result});
   Check(grid.Rows[0].Cells["evidence"].Value.ToString().Contains("실제로 선택한 자막 구절") && grid.Rows[0].Cells["evidence"].ToolTipText.Contains("선택한 자막 구절") && !grid.Rows[0].Cells["evidence"].ToolTipText.Contains("avoid_names"),"visible reference shows selected quote on one line and hides internal metadata in tooltip");
   accepted.FitEligible=false;
   typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{result});
   Check(grid.Rows.Count==0,"all rejected candidates produce no fabricated highest-score winner");
   result.ScoreError="合成評価失敗";
   typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{result});
   Check(grid.Rows.Count==0,"unverified production candidates are not exposed through ungraded fallback");
   form.Close();
  }
  return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex.ToString());return 1;}}
}
