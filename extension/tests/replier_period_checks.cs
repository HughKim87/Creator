using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Net;
using System.Threading;
using System.Windows.Forms;
using ReplierDesktop;
public static class PeriodChecks
{
    static void Check(bool ok,string name){if(!ok)throw new Exception(name);Console.WriteLine("PASS "+name);}
    [STAThread] public static int Main(string[] args)
    {
        try
        {
            ServicePointManager.SecurityProtocol=SecurityProtocolType.Tls12;
            string output=Path.GetFullPath(args[0]);Directory.CreateDirectory(output);
            string run=Path.Combine(output,"run-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(run);
            var store=new SettingsStore(Path.Combine(run,"settings.json"));
            Check(store.Load().UploadPeriod=="week","new installation defaults to recent week");
            foreach(string key in UploadPeriods.Keys){store.Save(new ReplierSettings{UploadPeriod=key});Check(new SettingsStore(Path.Combine(run,"settings.json")).Load().UploadPeriod==key,"period survives store reload: "+key);}
            Check(!VideoSearch.SearchUrl("게임","all").Contains("&sp="),"all-time search omits date filter");
            Check(VideoSearch.SearchUrl("게임","day").Contains("sp=EgIIAg%3D%3D"),"day filter encoded once");
            bool rejected=false;
            try{VideoSearch.Parse("var ytInitialData = {\"contents\":{}};","week");}catch(InvalidDataException){rejected=true;}
            Check(rejected,"restricted search fails closed when server does not confirm filter");
            Check(UploadPeriods.IncludesDisplayAge("23시간 전","day") && !UploadPeriods.IncludesDisplayAge("1일 전","day") && !UploadPeriods.IncludesDisplayAge("4일 전","day"),"day boundary excludes old mixed-in recommendations");
            Check(UploadPeriods.IncludesDisplayAge("6일 전","week") && !UploadPeriods.IncludesDisplayAge("1주 전","week"),"week boundary handled conservatively");
            Check(UploadPeriods.IncludesDisplayAge("4주 전","month") && !UploadPeriods.IncludesDisplayAge("1개월 전","month") && !UploadPeriods.IncludesDisplayAge("미제공","week"),"coarse or unknown dates do not leak into recent results");
            foreach(string period in new[]{"day","week","month"})
            {
                var videos=VideoSearch.Search("게임 리뷰",CancellationToken.None,period).GetAwaiter().GetResult();
                Check(videos.Count>0,"actual YouTube confirms upload filter and supplies videos: "+period);
                Check(videos.All(v=>UploadPeriods.IncludesDisplayAge(v.PublishedText,period)),"actual returned videos stay within selected age: "+period);
                Console.WriteLine("AGES "+period+": "+string.Join(", ",videos.Take(8).Select(v=>v.PublishedText)));
            }
            var batch=VideoBatch.Collect("게임 리뷰",new VideoLedger(Path.Combine(run,"live.jsonl")),new ContentStore(Path.Combine(run,"content")),CancellationToken.None,period:"week").GetAwaiter().GetResult();
            Check(batch.Videos.Count>0 && batch.Videos.Count<=10 && batch.Error.Length==0,"filtered actual video batch retains caption requirement and ten-video cap");
            Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
            string history=Path.Combine(run,"history.json");
            using(var form=new MainForm(history))
            {
                var combo=(ComboBox)form.Controls.Find("UploadPeriod",true)[0];
                foreach(int index in new[]{0,1,3,2}){combo.SelectedIndex=index;Check(store.Load().UploadPeriod==UploadPeriods.Keys[index],"native change saves immediately: "+UploadPeriods.Keys[index]);}
                using(var locked=new FileStream(Path.Combine(run,"settings.json.new"),FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None))
                {
                    combo.SelectedIndex=0;
                    Check(combo.SelectedIndex==2 && store.Load().UploadPeriod=="month","failed save restores prior selection and persisted setting");
                }
            }
            using(var reopened=new MainForm(history))
            {
                reopened.ShowInTaskbar=false;reopened.Opacity=0;reopened.Show();
                var combo=(ComboBox)reopened.Controls.Find("UploadPeriod",true)[0];
                Check(combo.SelectedIndex==2,"native window restart restores selected period");
                using(var bitmap=new Bitmap(reopened.Width,reopened.Height))
                {reopened.DrawToBitmap(bitmap,new Rectangle(0,0,bitmap.Width,bitmap.Height));bitmap.Save(Path.Combine(output,"period-preview.png"),ImageFormat.Png);}
                reopened.Close();
            }
            return 0;
        }catch(Exception ex){Console.Error.WriteLine(ex.GetType().Name+": "+ex.Message);return 1;}
    }
}