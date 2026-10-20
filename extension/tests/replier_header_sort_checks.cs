using System;using System.Collections.Generic;using System.Drawing;using System.Drawing.Imaging;using System.IO;using System.Linq;using System.Reflection;using System.Windows.Forms;using ReplierDesktop;
public static class HeaderSortChecks
{
 static void Check(bool ok,string label){if(!ok)throw new Exception(label);Console.WriteLine("PASS "+label);}
 static void Set(MainForm form,string name,object value){typeof(MainForm).GetField(name,BindingFlags.NonPublic|BindingFlags.Instance).SetValue(form,value);}
 static void Click(DataGridView grid,string column){typeof(DataGridView).GetMethod("OnColumnHeaderMouseClick",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(grid,new object[]{new DataGridViewCellMouseEventArgs(grid.Columns[column].Index,-1,0,0,new MouseEventArgs(MouseButtons.Left,1,0,0,0))});}
 static int[] IDs(DataGridView grid){return grid.Rows.Cast<DataGridViewRow>().Select(r=>int.Parse(((Video)r.Tag).Title)).ToArray();}
 [STAThread] public static int Main(string[] args){try{
  Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
  string output=Path.GetFullPath(args[0]);Directory.CreateDirectory(output);Exception error=null;
  using(var form=new MainForm(Path.Combine(output,"history.json"))){form.Opacity=0;form.ShowInTaskbar=false;
  form.Shown+=async(sender,e)=>{try{
   var videos=(DataGridView)form.Controls.Find("Videos",true)[0];var comments=(DataGridView)form.Controls.Find("Comments",true)[0];
   Set(form,"busy",true);string[] counts={"9개","100개","20개","1.2만개","미확인","사용 중지","0개"};
   var originals=new List<Video>();
   for(int i=0;i<counts.Length;i++){var video=new Video{Id="R"+i.ToString("D10"),Title=i.ToString(),CommentCountText=counts[i]};originals.Add(video);int row=videos.Rows.Add(video.Title,"채널","12:34",i==0?"1.2만회":"조회수 "+i+"회","1일 전",counts[i]);videos.Rows[row].Tag=video;}
   Set(form,"videos",originals);videos.ClearSelection();videos.Rows[2].Selected=true;var selected=videos.SelectedRows[0];
   Click(videos,"comments");
   Check(IDs(videos).SequenceEqual(new[]{3,1,2,0,6,4,5}),"comment-count header sorts numbers descending not lexicographically");
   Check(videos.Columns["comments"].HeaderCell.SortGlyphDirection==SortOrder.Descending,"comment count descending arrow matches order");
   Check(videos.SelectedRows[0]==selected && ((Video)selected.Tag).Title=="2","selection remains attached to same video during sort");
   Click(videos,"comments");
   Check(IDs(videos).SequenceEqual(new[]{6,0,2,1,3,4,5}),"second click toggles ascending with unknown and disabled counts still last");
   Check(videos.Columns["comments"].HeaderCell.SortGlyphDirection==SortOrder.Ascending,"ascending arrow matches second click");
   Click(videos,"views");Check(IDs(videos)[0]==0 && videos.Columns["comments"].HeaderCell.SortGlyphDirection==SortOrder.None,"view counts use numeric sort and clear prior header arrow");
   foreach(var value in new[]{"9점","100점","85점","미평가","0점"}){int row=comments.Rows.Add("검사 모델",value+" 댓글","00:01 · 대사",value);comments.Rows[row].Cells["evidence"].ToolTipText=value+" 근거";}
   Click(comments,"fit");
   Check(comments.Rows.Cast<DataGridViewRow>().Select(r=>r.Cells["fit"].Value.ToString()).SequenceEqual(new[]{"100점","85점","9점","0점","미평가"}),"fit header click sorts actual numeric scores descending");
   Click(comments,"fit");
   Check(comments.Rows.Cast<DataGridViewRow>().Select(r=>r.Cells["fit"].Value.ToString()).SequenceEqual(new[]{"0점","9점","85점","100점","미평가"}),"fit header toggles ascending with unscored last");
   Check(comments.Rows.Cast<DataGridViewRow>().All(r=>r.Cells["evidence"].ToolTipText==r.Cells["fit"].Value.ToString()+" 근거"),"fit sorting preserves comment and reference associations");
   Set(form,"busy",false);videos.ClearSelection();videos.Rows[0].Selected=true;await form.SelectionTask;
   var current=(Video)typeof(MainForm).GetField("currentVideo",BindingFlags.NonPublic|BindingFlags.Instance).GetValue(form);
   Check(object.ReferenceEquals(current,videos.Rows[0].Tag) && current.Id==originals[0].Id,"selecting sorted row resolves its video object rather than old row index");
   Check(form.Controls.Find("OpenVideo",true).Length==1 && form.Controls.Find("OpenVideo",true)[0].Enabled,"selected video has an enabled web video button independent of generation success");
   var good=new CommentSuggestion{Text="이걸 동시에 챙기네ㅋㅋ",TiePreference=2,TieReason="구어체 비교 선택",FitScore=81,GemmaFitScore=36,QwenFitScore=45,FitEligible=true,Evidence="시간 안에 동시에 조작합니다."};
   var broken=new CommentSuggestion{Text="미평가 후보",FitEligible=false,FitError="test"};
   var partial=new DualCommentResult{Complete=true,Batches=new List<ModelCommentBatch>{new ModelCommentBatch{Label="Gemma",Error="",Result=new CommentResult{Comments=new List<CommentSuggestion>{good,broken,new CommentSuggestion{Text="더 높은 적합도 설명형 후보",FitScore=90,FitEligible=true}},QualityFiltered=true}},new ModelCommentBatch{Label="Qwen",Error="",Result=new CommentResult{Comments=new List<CommentSuggestion>(),QualityFiltered=true}}}};
   typeof(MainForm).GetMethod("RenderComments",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(form,new object[]{partial});
   Check(comments.Rows.Count==1 && object.ReferenceEquals(comments.Rows[0].Tag,good),"failed candidates cannot hide the chosen natural final comment even when another eligible score is higher");
   var previousTask=form.SelectionTask;Click(videos,"comments");Check(object.ReferenceEquals(previousTask,form.SelectionTask),"header sort does not start or cancel comment generation");
   Check(form.Controls.Find("CommentStatus",true)[0].Text.Contains("소요") && form.Controls.Find("CommentStatus",true)[0].Text.Contains("초"),"completed selection including failure shows elapsed duration");
   Set(form,"busy",true);GridSorting.Sort(videos,"comments",true);Check(IDs(videos)[0]==3 && videos.Columns["comments"].HeaderCell.SortGlyphDirection==SortOrder.Descending,"fresh result defaults to descending comment count");

   using(var bitmap=new Bitmap(form.Width,form.Height)){form.DrawToBitmap(bitmap,new Rectangle(Point.Empty,bitmap.Size));bitmap.Save(Path.Combine(output,"header-sort-preview.png"),ImageFormat.Png);}
  }catch(Exception ex){error=ex;}finally{form.Close();}};Application.Run(form);}
  if(error!=null)throw error;return 0;
 }catch(Exception ex){Console.Error.WriteLine(ex.ToString());return 1;}}
}
