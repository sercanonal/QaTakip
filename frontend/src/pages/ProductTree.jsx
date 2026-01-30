import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  TreePine,
  Play,
  ChevronRight,
  ChevronDown,
  Server,
  Folder,
  FileCode,
  CheckCircle2,
  XCircle,
  Loader2,
  Layers,
  BarChart3,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "../lib/utils";
import api from "../lib/api";

const API_URL = process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_API_URL || "http://localhost:8001";

const ProductTree = () => {
  const { user } = useAuth();
  
  // Form state
  const [jiraTeamId, setJiraTeamId] = useState(() => localStorage.getItem("productTree_teamId") || "");
  const [reportDate, setReportDate] = useState(() => {
    const saved = localStorage.getItem("productTree_reportDate");
    if (saved) return saved;
    const today = new Date();
    return `${String(today.getDate()).padStart(2, '0')}/${String(today.getMonth() + 1).padStart(2, '0')}/${today.getFullYear()}`;
  });
  const [selectedProjects, setSelectedProjects] = useState(() => {
    const saved = localStorage.getItem("productTree_projectNames");
    return saved ? JSON.parse(saved) : ["FraudNG.UITests"];
  });
  const [days, setDays] = useState(() => localStorage.getItem("productTree_days") || "1");
  const [time, setTime] = useState(() => localStorage.getItem("productTree_time") || "00:00");
  
  // Analysis state
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [treeData, setTreeData] = useState(null);
  const [stats, setStats] = useState(null);
  
  // Save form values to localStorage
  useEffect(() => {
    localStorage.setItem("productTree_teamId", jiraTeamId);
    localStorage.setItem("productTree_reportDate", reportDate);
    localStorage.setItem("productTree_projectNames", JSON.stringify(selectedProjects));
    localStorage.setItem("productTree_days", days);
    localStorage.setItem("productTree_time", time);
  }, [jiraTeamId, reportDate, selectedProjects, days, time]);
  
  const handleProjectToggle = (projectValue) => {
    setSelectedProjects(prev => {
      if (prev.includes(projectValue)) {
        return prev.filter(p => p !== projectValue);
      } else {
        return [...prev, projectValue];
      }
    });
  };
  
  const runAnalysis = async () => {
    if (!jiraTeamId || !reportDate) {
      toast.error("Team ID ve tarih gerekli!");
      return;
    }
    
    setIsRunning(true);
    setLogs([]);
    setTreeData(null);
    setStats(null);
    
    try {
      const response = await fetch(`${API_URL}/api/product-tree/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jiraTeamId: parseInt(jiraTeamId),
          reportDate,
          projectNames: selectedProjects,
          days: parseInt(days),
          time
        })
      });
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";
        
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.log) {
                setLogs(prev => [...prev, data.log]);
              }
              
              if (data.complete) {
                if (data.tree) {
                  setTreeData(data.tree);
                  setStats(data.stats);
                } else if (data.cacheReady) {
                  // Fetch from cache
                  const cacheResponse = await fetch(`${API_URL}/api/product-tree/data`);
                  const cacheData = await cacheResponse.json();
                  if (cacheData.tree) {
                    setTreeData(cacheData.tree);
                    setStats(cacheData.stats);
                  }
                }
                toast.success("Analiz tamamlandı!");
              }
              
              if (data.error) {
                toast.error(data.error);
              }
            } catch (e) {
              console.error("Parse error:", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Analysis error:", error);
      toast.error("Analiz başlatılamadı: " + error.message);
    } finally {
      setIsRunning(false);
    }
  };
  
  return (
    <div className="space-y-6" data-testid="product-tree-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-600 flex items-center justify-center">
            <TreePine className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Test Kapsam Ağacı</h1>
            <p className="text-muted-foreground text-sm">Endpoint test coverage analizi</p>
          </div>
        </div>
      </div>
      
      {/* Form Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="w-5 h-5" />
            Analiz Parametreleri
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Team ID */}
            <div className="space-y-2">
              <Label htmlFor="teamId">Jira Team ID</Label>
              <Input
                id="teamId"
                type="number"
                placeholder="Örn: 123"
                value={jiraTeamId}
                onChange={(e) => setJiraTeamId(e.target.value)}
                data-testid="team-id-input"
              />
            </div>
            
            {/* Report Date */}
            <div className="space-y-2">
              <Label htmlFor="reportDate">Rapor Tarihi (GG/AA/YYYY)</Label>
              <Input
                id="reportDate"
                placeholder="10/12/2025"
                value={reportDate}
                onChange={(e) => setReportDate(e.target.value)}
                data-testid="report-date-input"
              />
            </div>
            
            {/* Days */}
            <div className="space-y-2">
              <Label htmlFor="days">Kaç Günlük</Label>
              <Input
                id="days"
                type="number"
                min="1"
                value={days}
                onChange={(e) => setDays(e.target.value)}
                data-testid="days-input"
              />
            </div>
            
            {/* Time */}
            <div className="space-y-2">
              <Label htmlFor="time">Saat Filtresi</Label>
              <Input
                id="time"
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                data-testid="time-input"
              />
            </div>
            
            {/* Projects */}
            <div className="space-y-2 col-span-full">
              <Label>Projeler</Label>
              <div className="flex flex-wrap gap-3">
                {PROJECT_OPTIONS.map((project) => (
                  <div key={project.value} className="flex items-center space-x-2">
                    <Checkbox
                      id={project.value}
                      checked={selectedProjects.includes(project.value)}
                      onCheckedChange={() => handleProjectToggle(project.value)}
                    />
                    <label
                      htmlFor={project.value}
                      className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                    >
                      {project.label}
                    </label>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          {/* Run Button */}
          <div className="mt-6">
            <Button
              onClick={runAnalysis}
              disabled={isRunning || !jiraTeamId || !reportDate}
              className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700"
              data-testid="run-analysis-btn"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Analiz Ediliyor...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Analizi Başlat
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* Logs */}
      {logs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">İşlem Logları</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-48 rounded border bg-muted/30 p-3">
              <div className="space-y-1 font-mono text-sm">
                {logs.map((log, i) => (
                  <div key={i} className="text-muted-foreground">{log}</div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
      
      {/* Stats */}
      {stats && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Genel İstatistikler
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
                <div className="text-2xl font-bold text-blue-600">{stats.totalEndpoints}</div>
                <div className="text-sm text-muted-foreground">Toplam Endpoint</div>
              </div>
              <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                <div className="text-2xl font-bold text-green-600">{stats.totalProjects}</div>
                <div className="text-sm text-muted-foreground">Toplam Proje</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Tree View */}
      {treeData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TreePine className="w-5 h-5" />
              Kapsam Ağacı
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg p-4 bg-background">
              {Object.entries(treeData).map(([projectName, project]) => (
                <TreeNode
                  key={projectName}
                  name={projectName}
                  data={project}
                  level={0}
                  type="project"
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Tree Node Component
const TreeNode = ({ name, data, level, type }) => {
  const [isExpanded, setIsExpanded] = useState(level < 1);
  
  const hasChildren = type === "project" ? data.apps && Object.keys(data.apps).length > 0
    : type === "app" ? data.controllers && Object.keys(data.controllers).length > 0
    : type === "controller" ? data.endPoints && data.endPoints.length > 0
    : false;
  
  const total = data.totalEndpoints || 0;
  const tested = data.testedEndpoints || 0;
  const percentage = total > 0 ? Math.round((tested / total) * 100) : 0;
  
  const getIcon = () => {
    switch (type) {
      case "project": return <Server className="w-4 h-4" />;
      case "app": return <Folder className="w-4 h-4" />;
      case "controller": return <FileCode className="w-4 h-4" />;
      default: return null;
    }
  };
  
  const getPercentageColor = () => {
    if (percentage >= 80) return "bg-green-500";
    if (percentage >= 50) return "bg-yellow-500";
    return "bg-red-500";
  };
  
  return (
    <div className={cn("", level > 0 && "ml-6 border-l border-border pl-4")}>
      <div
        className={cn(
          "flex items-center gap-2 p-2 rounded-lg cursor-pointer hover:bg-muted/50 transition-colors",
          level === 0 && "bg-muted/30"
        )}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {hasChildren ? (
          isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />
        ) : (
          <span className="w-4" />
        )}
        
        {getIcon()}
        
        <span className="font-medium truncate max-w-[300px]">{name}</span>
        
        <Badge className={cn("ml-auto", getPercentageColor())}>
          {percentage}%
        </Badge>
        
        <span className="text-sm text-muted-foreground whitespace-nowrap">
          {tested}/{data.newCalc || 0}/{total}
        </span>
      </div>
      
      {isExpanded && hasChildren && (
        <div className="mt-1">
          {type === "project" && data.apps && Object.entries(data.apps).map(([appName, appData]) => (
            <TreeNode key={appName} name={appName} data={appData} level={level + 1} type="app" />
          ))}
          
          {type === "app" && data.controllers && Object.entries(data.controllers).map(([ctrlName, ctrlData]) => (
            <TreeNode key={ctrlName} name={ctrlName} data={ctrlData} level={level + 1} type="controller" />
          ))}
          
          {type === "controller" && data.endPoints && data.endPoints.map((endpoint, idx) => (
            <EndpointNode key={idx} endpoint={endpoint} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
};

// Endpoint Node Component
const EndpointNode = ({ endpoint, level }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasTests = endpoint.tests && endpoint.tests.length > 0;
  
  const methodColors = {
    GET: "bg-green-500",
    POST: "bg-blue-500",
    PUT: "bg-orange-500",
    DELETE: "bg-red-500",
    PATCH: "bg-purple-500"
  };
  
  return (
    <div className={cn("ml-6 border-l border-border pl-4")}>
      <div
        className={cn(
          "flex items-center gap-2 p-2 rounded-lg cursor-pointer hover:bg-muted/50 transition-colors",
          "border border-border/50"
        )}
        onClick={() => hasTests && setIsExpanded(!isExpanded)}
      >
        {hasTests ? (
          isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />
        ) : (
          <span className="w-3" />
        )}
        
        <Badge className={cn("text-xs", methodColors[endpoint.method] || "bg-gray-500")}>
          {endpoint.method}
        </Badge>
        
        <code className="text-sm text-muted-foreground truncate max-w-[400px]">
          {endpoint.fullPath}
        </code>
        
        <div className="ml-auto flex items-center gap-2">
          {endpoint.isTested ? (
            <Badge variant="outline" className="text-green-600 border-green-600">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              Tested
            </Badge>
          ) : (
            <Badge variant="outline" className="text-red-600 border-red-600">
              <XCircle className="w-3 h-3 mr-1" />
              Not Tested
            </Badge>
          )}
          
          {hasTests && (
            <Badge variant="secondary">{endpoint.tests.length} test</Badge>
          )}
          
          {/* Test Type Badges */}
          <Badge className={endpoint.happy ? "bg-green-100 text-green-700" : "bg-orange-100 text-orange-700"}>
            ✅ HP
          </Badge>
          <Badge className={endpoint.alternatif ? "bg-green-100 text-green-700" : "bg-orange-100 text-orange-700"}>
            🔀 AS
          </Badge>
          <Badge className={endpoint.negatif ? "bg-green-100 text-green-700" : "bg-orange-100 text-orange-700"}>
            ❌ NS
          </Badge>
        </div>
      </div>
      
      {/* Tests */}
      {isExpanded && hasTests && (
        <div className="ml-6 mt-1 space-y-1">
          {endpoint.tests.map((test, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 p-2 rounded bg-muted/30 border border-border/30 text-sm"
            >
              <Badge className={test.status === "PASSED" ? "bg-green-500" : "bg-red-500"}>
                {test.status === "PASSED" ? "✓" : "✗"} {test.status}
              </Badge>
              <span className="font-medium truncate">{test.name || "Unnamed Test"}</span>
              <a
                href={`https://jira.intertech.com.tr/secure/Tests.jspa#/testCase/${test.key}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:underline ml-auto"
                onClick={(e) => e.stopPropagation()}
              >
                {test.key}
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProductTree;
