using System;using System.Collections.Generic;using System.Linq;using ReplierDesktop;
public static class ConnectionRubricChecks {
 static void Check(bool b,string s){if(!b)throw new Exception(s);Console.WriteLine("PASS "+s);}
 public static int Main(){try{var row=new CommentSuggestion{Text="분홍색과 라벤더 색깔이 예쁘네요"};var evidence=new[]{new KeyValuePair<string,CaptionCue>("c0",new CaptionCue{Text="핑크색도 있고 라벤더도 예쁘네요."})};
 var direct=ConnectionRubric.Parse("{\"connection\":\"direct_reaction\",\"evidence\":0}",row,evidence,"viewer");Check(direct.Eligible&&direct.Topic==18&&direct.Link==12&&direct.Score==45,"one direct-reaction decision always yields its topic/link rubric rather than an independent zero");
 Check(ConnectionRubric.Parse("{\"connection\":\"specific_reaction\",\"evidence\":0}",row,evidence,"viewer").Score==50,"specific contextual reaction uses the declared maximum rubric");Check(ConnectionRubric.Parse("{\"connection\":\"partial_reaction\",\"evidence\":0}",row,evidence,"viewer").Score==36,"partial relation retains a distinct lower rubric rather than receiving a passing-score floor");
 foreach(string level in new[]{"generic_reaction","retelling","unrelated","conflict"}){var r=ConnectionRubric.Parse("{\"connection\":\""+level+"\",\"evidence\":0}",row,evidence,"viewer");Check(!r.Eligible&&r.Score==0,"low or invalid relation remains rejected: "+level);}
 bool failed=false;try{ConnectionRubric.Parse("{\"connection\":\"direct_reaction\",\"evidence\":0,\"topic\":0}",row,evidence,"viewer");}catch(System.IO.InvalidDataException){failed=true;}Check(failed,"independent numeric scores cannot contradict or override the categorical contract");
 failed=false;try{ConnectionRubric.Parse("{\"connection\":\"direct_reaction\",\"evidence\":9}",row,evidence,"viewer");}catch(System.IO.InvalidDataException){failed=true;}Check(failed,"nonexistent reference cannot receive a rubric score");Check(!ConnectionRubric.Parse("{\"connection\":\"direct_reaction\",\"evidence\":0}",row,evidence,"awkward").Eligible,"a relevance category cannot bypass the independent voice veto");return 0;
 }catch(Exception e){Console.Error.WriteLine(e);return 1;}}
}
