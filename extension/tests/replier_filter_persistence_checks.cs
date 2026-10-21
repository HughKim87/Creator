using System;using System.IO;using System.Reflection;using System.Windows.Forms;using ReplierDesktop;
public static class FilterPersistenceChecks
{
 static void Check(bool ok,string text){if(!ok)throw new Exception(text);Console.WriteLine("PASS "+text);}
 static ComboBox Combo(MainForm f,string name){return (ComboBox)f.Controls.Find(name,true)[0];}
 [STAThread]public static int Main(string[] args){try{
 Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
 string output=Path.Combine(Path.GetFullPath(args[0]),Guid.NewGuid().ToString("N"));Directory.CreateDirectory(output);
 string history=Path.Combine(output,"history.json"),file=Path.Combine(output,"settings.json");var store=new SettingsStore(file);
 File.WriteAllText(file,"{\"UploadPeriod\":\"month\",\"CategoryId\":\"10\"}");
 Check(store.Load().SearchMode==1 && store.Load().UploadPeriod=="month" && store.Load().CategoryId=="10","legacy settings retain filters and default recommendation mode");
 for(int mode=0;mode<4;mode++){
  int period=mode;string category=mode%2==0?"20":"10";
  using(var f=new MainForm(history)){
   Combo(f,"SearchMode").SelectedIndex=mode;Combo(f,"UploadPeriod").SelectedIndex=period;Combo(f,"Category").SelectedIndex=VideoCategories.Index(category);
   ((TextBox)f.Controls.Find("Query",true)[0]).Text="직접 입력한 값은 복원하지 않음";
   bool saved=(bool)typeof(MainForm).GetMethod("SaveSearchSelection",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(f,new object[]{mode});Check(saved,"save acquisition filters: "+mode);
  }
  using(var f=new MainForm(history)){
   Check(Combo(f,"SearchMode").SelectedIndex==mode && Combo(f,"UploadPeriod").SelectedIndex==period && VideoCategories.All[Combo(f,"Category").SelectedIndex].Id==category,"restart restores recommendation/category/period together: "+mode);
   Check(((TextBox)f.Controls.Find("Query",true)[0]).Text=="" && !File.ReadAllText(file).Contains("직접 입력"),"typed input not stored or restored: "+mode);
  }
 }
 using(var f=new MainForm(history)){
  Combo(f,"SearchMode").SelectedIndex=2;((TextBox)f.Controls.Find("Query",true)[0]).Text="invalid-channel";
  f.AcquireVideos().GetAwaiter().GetResult();Check(store.Load().SearchMode==2,"actual acquisition saves selected mode before validating channel input");
 }
 using(var f=new MainForm(history)){
  Combo(f,"SearchMode").SelectedIndex=0;
  f.AcquireVideos().GetAwaiter().GetResult();Check(store.Load().SearchMode==0,"actual acquisition saves direct mode without requiring query persistence");
  using(var locked=new FileStream(file+".new",FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None)){
   bool saved=(bool)typeof(MainForm).GetMethod("SaveSearchSelection",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(f,new object[]{3});Check(!saved && store.Load().SearchMode==0,"save failure preserves previously persisted mode");
  }
 }
 store.Save(new ReplierSettings{SearchMode=1});bool rejected=false;try{store.Save(new ReplierSettings{SearchMode=4});}catch(InvalidDataException){rejected=true;}Check(rejected && store.Load().SearchMode==1,"invalid recommendation mode cannot replace saved settings");
 return 0;}catch(Exception ex){Console.Error.WriteLine(ex);return 1;}}
}
