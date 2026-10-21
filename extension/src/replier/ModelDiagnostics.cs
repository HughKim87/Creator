using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Web.Script.Serialization;
namespace ReplierDesktop
{
    public static class ModelDiagnostics
    {
        static readonly object gate=new object();
        public static void Record(string runtime,object record)
        {
            if(!Path.IsPathRooted(runtime))return;
            try
            {
                string file=Path.Combine(CreatorWorkspace.StateDirectory(),"llm-diagnostics.jsonl");
                lock(gate)
                {
                    Directory.CreateDirectory(Path.GetDirectoryName(file));
                    if(File.Exists(file) && new FileInfo(file).Length>2*1024*1024){var lines=File.ReadAllLines(file);File.WriteAllLines(file,lines.Skip(lines.Length/2),new UTF8Encoding(false));}
                    File.AppendAllText(file,new JavaScriptSerializer().Serialize(record)+Environment.NewLine,new UTF8Encoding(false));
                }
            }
            catch(IOException){}catch(UnauthorizedAccessException){}
        }
        public static double Seconds(object root,string key)
        {
            double value;return double.TryParse(Convert.ToString(CaptionService.Get(root,key)),out value)?Math.Round(value/1e9,3):0;
        }
    }
}
