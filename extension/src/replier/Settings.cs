using System;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;

namespace ReplierDesktop
{
    public static class UploadPeriods
    {
        public static readonly string[] Keys = { "day", "week", "month", "all" };
        public static readonly string[] Labels = { "최근 24시간", "최근 1주일", "최근 1개월", "전체 기간" };
        public static int Index(string key) { return Array.IndexOf(Keys,key); }
        public static string Filter(string key)
        {
            switch(key) { case "day": return "EgIIAg=="; case "week": return "EgIIAw==";
                case "month": return "EgIIBA=="; case "all": return "";
                default: throw new ArgumentException("업로드 기간 설정을 확인해 주세요."); }
        }
        public static bool IncludesDisplayAge(string text,string key)
        {
            if(Index(key)<0) throw new ArgumentException("업로드 기간 설정을 확인해 주세요.");
            if(key=="all") return true;
            var match=Regex.Match(text ?? "",@"(\d+)\s*(초|분|시간|일|주|개월|년)\s*전");
            long count;
            if(!match.Success || !long.TryParse(match.Groups[1].Value,out count)) return false;
            double hours;
            switch(match.Groups[2].Value)
            {
                case "초": hours=count/3600.0; break;
                case "분": hours=count/60.0; break;
                case "시간": hours=count; break;
                case "일": hours=count*24.0; break;
                case "주": hours=count*168.0; break;
                // Coarse month/year labels cannot prove membership in any supported recent period.
                default: return false;
            }
            return hours < (key=="day" ? 24 : key=="week" ? 168 : 720);
        }
        public static string YouTubeLabel(string key)
        {
            switch(key) { case "day": return "오늘"; case "week": return "이번 주";
                case "month": return "이번 달"; case "all": return "";
                default: throw new ArgumentException("업로드 기간 설정을 확인해 주세요."); }
        }
    }
    public sealed class ReplierSettings
    {
        public int SearchMode { get; set; }
        public string UploadPeriod { get; set; }
        public string CategoryId { get; set; }
        public ReplierSettings() { SearchMode=1; UploadPeriod = "week"; CategoryId = "20"; }
    }
    public sealed class SettingsStore
    {
        readonly string path;
        public SettingsStore(string file) { path = file; }
        public ReplierSettings Load()
        {
            if(!File.Exists(path)) return new ReplierSettings();
            var settings = new JavaScriptSerializer().Deserialize<ReplierSettings>(File.ReadAllText(path,Encoding.UTF8));
            if(settings == null || settings.SearchMode<0 || settings.SearchMode>3 || UploadPeriods.Index(settings.UploadPeriod)<0 || VideoCategories.Index(settings.CategoryId)<0)
                throw new InvalidDataException("저장한 필터 설정을 읽지 못했습니다.");
            return settings;
        }
        public void Save(ReplierSettings settings)
        {
            if(settings == null || settings.SearchMode<0 || settings.SearchMode>3 || UploadPeriods.Index(settings.UploadPeriod)<0 || VideoCategories.Index(settings.CategoryId)<0) throw new InvalidDataException("필터 설정이 올바르지 않습니다.");
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            string temp = path + ".new";
            File.WriteAllText(temp,new JavaScriptSerializer().Serialize(settings),new UTF8Encoding(false));
            if(File.Exists(path)) File.Replace(temp,path,null); else File.Move(temp,path);
        }
    }
}