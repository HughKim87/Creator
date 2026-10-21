using System;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;

namespace ReplierDesktop
{
    public static class CreatorWorkspace
    {
        public static string ExtensionRoot()
        {
            var directory = new DirectoryInfo(AppDomain.CurrentDomain.BaseDirectory);
            while(directory != null)
            {
                string extension = Path.Combine(directory.FullName,"extension");
                if(File.Exists(Path.Combine(directory.FullName,"PROJECT_RULES.md")) && Directory.Exists(extension)) return extension;
                directory=directory.Parent;
            }
            throw new DirectoryNotFoundException("Creator main workspace was not found.");
        }
        public static string Runtime(string component)
        {
            string extension=ExtensionRoot();
            var catalog=new JavaScriptSerializer().DeserializeObject(File.ReadAllText(Path.Combine(extension,"config","workspace-runtime.json"),Encoding.UTF8));
            var entry=CaptionService.Get(CaptionService.Get(catalog,"components"),component);
            string root=Path.Combine(extension,".runtime");
            string target=Path.GetFullPath(Path.Combine(root,Convert.ToString(CaptionService.Get(entry,"path")).Replace('/',Path.DirectorySeparatorChar)));
            if(!target.StartsWith(root+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase))throw new InvalidDataException("Unsafe runtime path.");
            if(Directory.Exists(target))return target;
            foreach(var old in (object[])CaptionService.Get(entry,"legacy"))
            {
                string legacy=Path.GetFullPath(Path.Combine(root,Convert.ToString(old).Replace('/',Path.DirectorySeparatorChar)));
                if(!legacy.StartsWith(root+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase))throw new InvalidDataException("Unsafe runtime path.");
                if(Directory.Exists(legacy))return legacy;
            }
            return target;
        }
        public static string StateDirectory()
        {
            string job=Environment.GetEnvironmentVariable("CREATOR_JOB_ID");
            if(String.IsNullOrEmpty(job))return Path.Combine(ExtensionRoot(),"data","replier");
            if(!Regex.IsMatch(job,@"\A[a-z0-9](?:[a-z0-9-]{0,78}[a-z0-9])?\z") ||
               Regex.IsMatch(job,@"\A(?:con|prn|aux|nul|com[0-9]|lpt[0-9])\z"))throw new InvalidDataException("Invalid job ID.");
            return Path.Combine(ExtensionRoot(),"jobs",job,"work","replier");
        }
    }
}
