using System;
using System.IO;
using ReplierDesktop;
public static class WorkspaceChecks
{
    public static int Main()
    {
        string original=Environment.GetEnvironmentVariable("CREATOR_JOB_ID");
        try
        {
            Environment.SetEnvironmentVariable("CREATOR_JOB_ID","video-a");
            string first=CreatorWorkspace.StateDirectory();
            Environment.SetEnvironmentVariable("CREATOR_JOB_ID","video-b");
            string second=CreatorWorkspace.StateDirectory();
            if(first==second || !first.EndsWith(Path.Combine("video-a","work","replier")))throw new Exception("job state collision");
            foreach(string bad in new[]{"../other","con","video-","A"})
            {
                Environment.SetEnvironmentVariable("CREATOR_JOB_ID",bad);
                bool rejected=false;
                try{CreatorWorkspace.StateDirectory();}catch(InvalidDataException){rejected=true;}
                if(!rejected)throw new Exception("unsafe job accepted");
            }
            if(!CreatorWorkspace.Runtime("replier-desktop").StartsWith(Path.Combine(CreatorWorkspace.ExtensionRoot(),".runtime")))throw new Exception("runtime escaped");
            Console.WriteLine("PASS Replier job state isolation, identifier boundaries and shared runtime resolution");
            return 0;
        }
        finally{Environment.SetEnvironmentVariable("CREATOR_JOB_ID",original);}
    }
}
