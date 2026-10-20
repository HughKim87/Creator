using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Net;
using System.Reflection;
using System.Threading;
using System.Windows.Forms;
using ReplierDesktop;
public static class CommentUiChecks
{
    static void Check(bool ok,string message){if(!ok)throw new Exception(message);Console.WriteLine("PASS "+message);}
    static void Set(MainForm form,string field,object value){typeof(MainForm).GetField(field,BindingFlags.Instance|BindingFlags.NonPublic).SetValue(form,value);}
    static bool CombinedScore(DataGridViewRow row)
    {
        var match=System.Text.RegularExpressions.Regex.Match(row.Cells["fit"].ToolTipText,@"Gemma (\d+)/50[\s\S]*?\r?\nQwen (\d+)/50");
        int total;
        if(!match.Success || !int.TryParse(row.Cells["fit"].Value.ToString().Replace("점",""),out total)) return false;
        int g=int.Parse(match.Groups[1].Value),q=int.Parse(match.Groups[2].Value);
        return g>=0 && g<=50 && q>=0 && q<=50 && total==g+q;
    }
    [STAThread] public static int Main(string[] args)
    {
        try
        {
            ServicePointManager.SecurityProtocol=SecurityProtocolType.Tls12;
            string output=Path.GetFullPath(args[0]);Directory.CreateDirectory(output);
            string run=Path.Combine(output,"run-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(run);
            var video=VideoSearch.Search("인디 게임 추천",CancellationToken.None).GetAwaiter().GetResult().First(v=>v.Id=="HPUpsEzL1ps");
            var content=CaptionService.Fetch(video,CancellationToken.None).GetAwaiter().GetResult();
            new ContentStore(Path.Combine(run,"content")).Save(content);
            Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
            Exception error=null;
            using(var form=new MainForm(Path.Combine(run,"history.json")))
            {
                form.ShowInTaskbar=false;form.Opacity=0;
                form.Shown+=async(sender,e)=>{
                    try
                    {
                        var grid=(DataGridView)form.Controls.Find("Videos",true)[0];
                        Check(grid.Columns[2].HeaderText=="영상 길이" && grid.Columns[3].HeaderText=="조회수","native list shows duration and views");
                        Check(form.Controls.Find("VideoThumbnail",true).Length==0 && form.Controls.Find("VideoTitle",true).Length==0 && form.Controls.Find("OpenVideo",true).Length==0,"selected video information card removed");
                        Check(grid.Columns[4].HeaderText=="업로드","published time column visible");
                        var refresh=(Button)form.Controls.Find("RefreshComments",true)[0];
                        Check(!refresh.Enabled,"refresh disabled without selected video");
                        Set(form,"busy",true);Set(form,"videos",new List<Video>{video});
                        int row=grid.Rows.Add(video.Title,video.Channel,video.DurationText,video.ViewCountText,video.PublishedText);
                        grid.Rows[row].Tag=video;
                        grid.ClearSelection();Set(form,"busy",false);
                        var comments=(DataGridView)form.Controls.Find("Comments",true)[0];
                        Check(comments.Rows.Count==0,"no generation before selection");
                        grid.Rows[0].Selected=true;
                        await form.SelectionTask;
                        Check(comments.Rows.Count==1,"selecting native video row displays one highest scored local AI comment");
                        Check(comments.Rows.Cast<DataGridViewRow>().All(CombinedScore),"real winner score equals Gemma fifty-point plus Qwen fifty-point assessments");
                        Check(comments.Rows.Cast<DataGridViewRow>().All(r=>r.Cells["evidence"].Value.ToString().Contains(" · ")),"native comments include subtitle timestamps and quotes");
                        Check(new[]{"Gemma","Qwen"}.Contains(comments.Rows[0].Cells["model"].Value.ToString()),"winner retains model attribution");
                        Check(((Label)form.Controls.Find("CommentStatus",true)[0]).Text=="적합도 최고 댓글 1개","completed status describes one winner");
                        Check(refresh.Enabled,"refresh enabled after generation");
                        var oldWinner=comments.Rows[0].Tag;
                        refresh.PerformClick();
                        Check(!refresh.Enabled,"refresh disabled while local model is running");
                        await form.SelectionTask;
                        Check(comments.Rows.Count==1 && !object.ReferenceEquals(comments.Rows[0].Tag,oldWinner),"refresh replaces winner using newly generated candidates");
                        Check(grid.Rows[0].Selected && refresh.Enabled,"refresh retains video selection and restores button");
                        Check(comments.Rows.Cast<DataGridViewRow>().All(CombinedScore),"refreshed comments receive both model assessments and matching totals");
                        var totals=comments.Rows.Cast<DataGridViewRow>().Select(r=>int.Parse(r.Cells["fit"].Value.ToString().Replace("점",""))).ToArray();
                        Check(totals.SequenceEqual(totals.OrderByDescending(x=>x)),"actual combined scores remain sorted descending");
                        using(var bitmap=new Bitmap(form.Width,form.Height)){
                            form.DrawToBitmap(bitmap,new Rectangle(0,0,bitmap.Width,bitmap.Height));
                            bitmap.Save(Path.Combine(output,"comments-preview.png"),ImageFormat.Png);
                        }
                        var first=comments.Rows[0].Cells["text"].Value.ToString();
                        await form.ShowSelectedVideo();
                        Check(comments.Rows.Count==1 && CombinedScore(comments.Rows[0]),"repeat selection grades cached candidates and displays one winner");
                    }
                    catch(Exception ex){error=ex;}
                    finally{form.Close();}
                };
                Application.Run(form);
            }
            if(error!=null)throw error;
            return 0;
        }
        catch(Exception ex){Console.Error.WriteLine(ex.GetType().Name+": "+ex.Message);return 1;}
    }
}