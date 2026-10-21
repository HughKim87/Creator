using System;
using System.Drawing;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace ReplierDesktop
{
    public sealed class YoutubeConnectionDialog : Form
    {
        readonly IYoutubePublisher publisher;
        readonly Func<string> pickFile;
        readonly CancellationTokenSource lifetime=new CancellationTokenSource();
        readonly Label account=new Label(),status=new Label();
        readonly Button connect=new Button(),restore=new Button(),disconnect=new Button();
        bool working;
        public Task OperationTask {get;private set;}
        public YoutubeConnectionDialog(IYoutubePublisher service,Func<string> filePicker=null)
        {
            publisher=service;pickFile=filePicker ?? PickFile;OperationTask=Task.FromResult(0);
            Name="YoutubeConnection";Text="유튜브 연결";Font=new Font("맑은 고딕",10);
            ClientSize=new Size(540,230);MinimumSize=new Size(440,260);StartPosition=FormStartPosition.CenterParent;
            ShowInTaskbar=false;MinimizeBox=false;MaximizeBox=false;
            var panel=new TableLayoutPanel{Dock=DockStyle.Fill,Padding=new Padding(16),ColumnCount=1,RowCount=5};
            panel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
            foreach(int h in new[]{50,42,0,34,38})panel.RowStyles.Add(h==0 ? new RowStyle(SizeType.Percent,100) : new RowStyle(SizeType.Absolute,h));
            Controls.Add(panel);
            account.Name="ConnectedAccount";account.Dock=DockStyle.Fill;account.AutoEllipsis=true;panel.Controls.Add(account,0,0);
            var buttons=new FlowLayoutPanel{Dock=DockStyle.Fill,WrapContents=false,AutoScroll=true};
            connect.Name="ConnectYoutube";connect.Text="연결 파일 선택";connect.AutoSize=true;
            restore.Name="RestoreYoutube";restore.Text="저장된 연결 사용";restore.AutoSize=true;
            disconnect.Name="DisconnectYoutube";disconnect.Text="연결 해제";disconnect.AutoSize=true;
            buttons.Controls.AddRange(new Control[]{connect,restore,disconnect});panel.Controls.Add(buttons,0,1);
            status.Name="ConnectionStatus";status.Dock=DockStyle.Fill;status.AutoEllipsis=true;panel.Controls.Add(status,0,2);
            var help=new LinkLabel{Text="처음 연결하는 방법",AutoSize=true};panel.Controls.Add(help,0,3);
            help.LinkClicked+=(sender,e)=>YoutubePostDialog.ShowSetupHelp(this);
            var close=new Button{Name="CloseConnection",Text="닫기",Dock=DockStyle.Right,Width=80};panel.Controls.Add(close,0,4);
            close.Click+=(sender,e)=>Close();
            connect.Click+=(sender,e)=>{if(working)return;string file=pickFile();if(file!=null)OperationTask=Run(()=>publisher.Connect(file,lifetime.Token));};
            restore.Click+=(sender,e)=>{OperationTask=Run(()=>publisher.Restore(lifetime.Token));};
            disconnect.Click+=(sender,e)=>{
                if(working)return;
                try{publisher.Disconnect();status.Text="이 앱의 연결을 해제했습니다.";}catch{status.Text="저장된 연결을 해제하지 못했습니다.";}
                UpdateControls();
            };
            FormClosing+=(sender,e)=>lifetime.Cancel();
            Shown+=(sender,e)=>{
                var area=Screen.FromControl(this).WorkingArea;
                MinimumSize=new Size(Math.Min(MinimumSize.Width,area.Width-16),Math.Min(MinimumSize.Height,area.Height-16));
                Size=new Size(Math.Min(Width,area.Width-16),Math.Min(Height,area.Height-16));
                Left=Math.Max(area.Left,Math.Min(Left,area.Right-Width));Top=Math.Max(area.Top,Math.Min(Top,area.Bottom-Height));
            };
            UpdateControls();
        }
        string PickFile()
        {
            using(var picker=new OpenFileDialog{Title="다운로드한 Google 연결 JSON 파일 선택",Filter="연결 파일 (*.json)|*.json",CheckFileExists=true})
                return picker.ShowDialog(this)==DialogResult.OK ? picker.FileName : null;
        }
        void UpdateControls()
        {
            if(IsDisposed)return;
            account.Text=publisher.Account==null ? "유튜브 · 연결 안 됨" : "연결된 채널 · "+publisher.Account.Title+"\n"+publisher.Account.Id;
            connect.Enabled=restore.Enabled=!working;disconnect.Enabled=!working && publisher.Account!=null;
        }
        async Task Run(Func<Task> action)
        {
            if(working)return;working=true;status.Text="연결 중… 브라우저가 열리면 로그인해 주세요.";UpdateControls();
            try{await action();if(!IsDisposed)status.Text="연결되었습니다. 이 계정으로 채널 추천과 댓글 게시를 사용할 수 있습니다.";}
            catch(Exception ex){if(!IsDisposed)status.Text=ex is InvalidOperationException ? ex.Message : "연결하지 못했습니다. 설정과 인터넷 연결을 확인해 주세요.";}
            finally{working=false;if(!IsDisposed)UpdateControls();}
        }
    }
}
