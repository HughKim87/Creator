using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using System.Windows.Forms;

namespace ReplierDesktop
{
    public static class GridSorting
    {
        public static long? DisplayNumber(object value)
        {
            string text=Convert.ToString(value);
            text=Regex.Replace(text,@"\s*(?:개|점)$","");
            long number=ViewCounts.Parse(text);
            return number<0 ? (long?)null : number;
        }
        sealed class Rows : IComparer
        {
            readonly string column;
            readonly bool descending;
            readonly Dictionary<DataGridViewRow,int> positions;
            public Rows(string name,bool desc,Dictionary<DataGridViewRow,int> order)
            {column=name;descending=desc;positions=order;}
            public int Compare(object a,object b)
            {
                var first=(DataGridViewRow)a;var second=(DataGridViewRow)b;
                long? x=DisplayNumber(first.Cells[column].Value),y=DisplayNumber(second.Cells[column].Value);
                if(x.HasValue!=y.HasValue)return x.HasValue ? -1 : 1;
                int comparison=x.HasValue ? x.Value.CompareTo(y.Value) : 0;
                if(comparison!=0)return descending ? -comparison : comparison;
                return positions[first].CompareTo(positions[second]);
            }
        }
        public static void Toggle(DataGridView grid,string column)
        {
            bool descending=grid.Columns[column].HeaderCell.SortGlyphDirection!=SortOrder.Descending;
            Sort(grid,column,descending);
        }
        public static void Sort(DataGridView grid,string column,bool descending)
        {
            var order=grid.Rows.Cast<DataGridViewRow>().Select((row,index)=>new {row,index}).ToDictionary(x=>x.row,x=>x.index);
            var selected=grid.SelectedRows.Cast<DataGridViewRow>().FirstOrDefault();
            grid.Sort(new Rows(column,descending,order));
            foreach(DataGridViewColumn item in grid.Columns)item.HeaderCell.SortGlyphDirection=SortOrder.None;
            grid.Columns[column].HeaderCell.SortGlyphDirection=descending ? SortOrder.Descending : SortOrder.Ascending;
            if(selected!=null){grid.ClearSelection();selected.Selected=true;}
        }
    }
}
