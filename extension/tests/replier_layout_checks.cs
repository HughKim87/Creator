using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Windows.Forms;
using ReplierDesktop;
public static class LayoutChecks
{
 static void Check(bool ok,string label){if(!ok)throw new Exception(label);Console.WriteLine("PASS "+label);}
 static void Pump(Form form){form.PerformLayout();Application.DoEvents();}
 [STAThread] public static int Main(string[] args)
 {
  try{
   Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
   string output=Path.GetFullPath(args[0]);Directory.CreateDirectory(output);
   using(var form=new MainForm(Path.Combine(output,"layout-history.json"))){
    form.ShowInTaskbar=false;form.Opacity=0;form.Show();Pump(form);
    Check(Screen.FromControl(form).WorkingArea.Contains(form.Bounds),"initial window stays inside actual working area after DPI scaling");
    var split=(SplitContainer)form.Controls.Find("ListSplit",true)[0];
    var videos=(DataGridView)form.Controls.Find("Videos",true)[0];
    var comments=(DataGridView)form.Controls.Find("Comments",true)[0];
    for(int i=0;i<30;i++){
     videos.Rows.Add("스크롤 확인 영상 "+i,"채널","12:34","123,456회","1일 전");
     comments.Rows.Add(i%2==0?"Gemma":"Qwen","이런 건 구경하다 보면 시간 가는 줄 모르겠네요. 작은 화면에서도 댓글을 읽을 수 있어야 합니다. "+i,"00:01 · 참고 자막 구간 "+i);
    }
    foreach(var size in new[]{new Size(800,600),new Size(1024,720)}){
     form.Size=size;Pump(form);
     Check(form.Size==size,"window can shrink to "+size);
     foreach(var control in new Control[]{videos,comments,form.Controls.Find("Recommend",true)[0],form.Controls.Find("SearchMode",true)[0],form.Controls.Find("Query",true)[0],form.Controls.Find("RefreshComments",true)[0],form.Controls.Find("PostComment",true)[0]}){
      var rect=form.RectangleToClient(control.RectangleToScreen(control.ClientRectangle));
      Check(form.ClientRectangle.Contains(rect) && rect.Height>20,"control stays visible at "+size+": "+control.Name);
     }
     Check(videos.Height>=70 && comments.Height>=70,"both lists keep useful height at "+size);
     videos.FirstDisplayedScrollingRowIndex=29;comments.FirstDisplayedScrollingRowIndex=29;Pump(form);
     Check(videos.Rows[29].Displayed && comments.Rows[29].Displayed,"both lists independently scroll to final row at "+size);
     int prior=split.SplitterDistance;
     split.SplitterDistance=prior+20;Pump(form);
     Check(split.SplitterDistance==prior+20,"divider adjusts list heights at "+size);
     using(var bitmap=new Bitmap(form.Width,form.Height)){
      form.DrawToBitmap(bitmap,new Rectangle(Point.Empty,bitmap.Size));
      bitmap.Save(Path.Combine(output,"layout-"+size.Width+"x"+size.Height+".png"),ImageFormat.Png);
     }
    }
    form.Scale(new SizeF(1.5f,1.5f));
    typeof(MainForm).GetMethod("FitToWorkingArea",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic).Invoke(form,new object[]{true});
    Pump(form);
    Check(Screen.FromControl(form).WorkingArea.Contains(form.Bounds),"scaled layout clamps to actual working area");
    foreach(var control in new Control[]{videos,comments,form.Controls.Find("Recommend",true)[0],form.Controls.Find("SearchMode",true)[0],form.Controls.Find("Query",true)[0],form.Controls.Find("RefreshComments",true)[0],form.Controls.Find("PostComment",true)[0]}){
     var rect=form.RectangleToClient(control.RectangleToScreen(control.ClientRectangle));
     Check(form.ClientRectangle.Contains(rect) && rect.Height>20,"scaled control remains inside window: "+control.Name);
    }
    form.Close();
   }
   return 0;
  }catch(Exception ex){Console.Error.WriteLine(ex.ToString());return 1;}
 }
}

