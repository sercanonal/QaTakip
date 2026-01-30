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
  RefreshCw,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "../lib/utils";
import api from "../lib/api";

const API_URL = process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_API_URL || "http://localhost:8001";

const ProductTree = () => {
  const { user } = useAuth();
  
  // QA Projects from settings
  const [qaProjects, setQaProjects] = useState([]);
  
  // Form state
  const [jiraTeamId, setJiraTeamId] = useState(() => localStorage.getItem("productTree_teamId") || "");
  const [reportDate, setReportDate] = useState(() => {
    const saved = localStorage.getItem("productTree_reportDate");
    if (saved) return saved;
    const today = new Date();
    return `${String(today.getDate()).padStart(2, '0')}/${String(today.getMonth() + 1).padStart(2, '0')}/${today.getFullYear()}`;
  });
  const [selectedProject, setSelectedProject] = useState(() => localStorage.getItem("productTree_selectedProject") || "");
  const [days, setDays] = useState(() => localStorage.getItem("productTree_days") || "1");
  const [time, setTime] = useState(() => localStorage.getItem("productTree_time") || "00:00");
  
  // Analysis state
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [treeData, setTreeData] = useState(null);
  const [stats, setStats] = useState(null);

  // Refresh controller endpoints function
  const handleRefreshEndpoints = async (controllerName, controllerData) => {
    if (!controllerData.endPoints || controllerData.endPoints.length === 0) {
      toast.info("Bu controller'da endpoint bulunamadı");
      return;
    }
    
    toast.info(`${controllerName} için TOAY listesi yenileniyor...`);
    
    try {
      // Re-run analysis for this specific controller's endpoints
      const response = await api.post("/product-tree/refresh-controller", {
        controllerName,
        endPoints: controllerData.endPoints,
        jiraTeamId,
        reportDate,
        days,
        time
      });
      
      if (response.data.success) {
        // Update the tree data with refreshed endpoints
        setTreeData(prevTree => {
          const newTree = JSON.parse(JSON.stringify(prevTree));
          
          // Find and update the controller in the tree
          Object.values(newTree).forEach(project => {
            if (project.apps) {
              Object.values(project.apps).forEach(app => {
                if (app.controllers && app.controllers[controllerName]) {
                  app.controllers[controllerName].endPoints = response.data.endPoints;
                  // Recalculate stats
                  const endpoints = response.data.endPoints;
                  app.controllers[controllerName].totalEndpoints = endpoints.length;
                  app.controllers[controllerName].testedEndpoints = endpoints.filter(e => e.isTested).length;
                }
              });
            }
          });
          
          return newTree;
        });
        
        toast.success(`${controllerName} güncellendi!`);
      } else {
        toast.error(response.data.error || "Yenileme başarısız");
      }
    } catch (error) {
      console.error("Refresh error:", error);
      toast.error("TOAY listesi yenilenemedi");
    }
  };
  
  // Fetch QA projects from settings
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await api.get("/qa-projects");
        console.log("QA Projects response:", response.data);
        
        // API returns {projects: [...]} format
        const projects = response.data?.projects || response.data || [];
        const projectsList = Array.isArray(projects) ? projects : [];
        
        console.log("Projects list:", projectsList);
        setQaProjects(projectsList);
        
        // Auto-select first project if none selected
        if (!selectedProject && projectsList.length > 0) {
          setSelectedProject(projectsList[0].name);
        }
      } catch (error) {
        console.error("Error fetching QA projects:", error);
      }
    };
    fetchProjects();
  }, [selectedProject]);
  
  // Save form values to localStorage
  useEffect(() => {
    localStorage.setItem("productTree_teamId", jiraTeamId);
    localStorage.setItem("productTree_reportDate", reportDate);
    localStorage.setItem("productTree_selectedProject", selectedProject);
    localStorage.setItem("productTree_days", days);
    localStorage.setItem("productTree_time", time);
  }, [jiraTeamId, reportDate, selectedProject, days, time]);
  
  const runAnalysis = async () => {
    if (!jiraTeamId || !reportDate || !selectedProject) {
      toast.error("Team ID, tarih ve proje seçimi gerekli!");
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
          projectNames: [selectedProject], // Single project as array
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
            
            {/* Project Selection - Single select from QA Projects */}
            <div className="space-y-2 col-span-full">
              <Label htmlFor="project">Proje Seçimi</Label>
              <Select value={selectedProject} onValueChange={setSelectedProject}>
                <SelectTrigger data-testid="project-select">
                  <SelectValue placeholder="Proje seçin..." />
                </SelectTrigger>
                <SelectContent>
                  {qaProjects.length > 0 ? (
                    qaProjects
                      .filter(project => project && project.name) // Filter out invalid projects
                      .map((project) => (
                        <SelectItem key={project.name} value={project.name}>
                          {project.name}
                        </SelectItem>
                      ))
                  ) : (
                    <div className="py-2 px-3 text-sm text-muted-foreground">
                      Proje bulunamadı - Ayarlardan ekleyin
                    </div>
                  )}
                </SelectContent>
              </Select>
              {qaProjects.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  Proje listesi Ayarlar sayfasından yönetilir.
                </p>
              )}
            </div>
          </div>
          
          {/* Run Button */}
          <div className="mt-6">
            <Button
              onClick={runAnalysis}
              disabled={isRunning || !jiraTeamId || !reportDate || !selectedProject}
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
                  onRefreshEndpoints={handleRefreshEndpoints}
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
const TreeNode = ({ name, data, level, type, onRefreshEndpoints }) => {
  const [isExpanded, setIsExpanded] = useState(level < 1);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const hasChildren = type === "project" ? data.apps && Object.keys(data.apps).length > 0
    : type === "app" ? data.controllers && Object.keys(data.controllers).length > 0
    : type === "controller" ? data.endPoints && data.endPoints.length > 0
    : false;
  
  // Calculate coverage based on 3 required test types per endpoint
  const calculateCoverage = () => {
    if (type === "controller" && data.endPoints) {
      let totalRequired = data.endPoints.length * 3; // 3 test types per endpoint
      let totalPassed = 0;
      
      // Helper functions to check test types
      const isHappyTest = (t) => {
        const name = (t.name || '').toLowerCase();
        const testType = (t.testType || t.type || '').toLowerCase();
        return name.includes('happy') || testType.includes('happy');
      };
      
      const isAlternatifTest = (t) => {
        const name = (t.name || '').toLowerCase();
        const testType = (t.testType || t.type || '').toLowerCase();
        return name.includes('alternatif') || name.includes('alternative') || 
               testType.includes('alternatif') || testType.includes('alternative');
      };
      
      const isNegatifTest = (t) => {
        const name = (t.name || '').toLowerCase();
        const testType = (t.testType || t.type || '').toLowerCase();
        return name.includes('negatif') || name.includes('negative') ||
               testType.includes('negatif') || testType.includes('negative');
      };
      
      data.endPoints.forEach(endpoint => {
        const hasHappy = endpoint.tests?.some(t => 
          isHappyTest(t) && t.status === 'PASSED'
        ) || endpoint.happy;
        const hasAlternatif = endpoint.tests?.some(t => 
          isAlternatifTest(t) && t.status === 'PASSED'
        ) || endpoint.alternatif;
        const hasNegatif = endpoint.tests?.some(t => 
          isNegatifTest(t) && t.status === 'PASSED'
        ) || endpoint.negatif;
        
        if (hasHappy) totalPassed++;
        if (hasAlternatif) totalPassed++;
        if (hasNegatif) totalPassed++;
      });
      
      return {
        total: totalRequired,
        passed: totalPassed,
        percentage: totalRequired > 0 ? Math.round((totalPassed / totalRequired) * 100) : 0
      };
    }
    
    // For project/app levels, use the original calculation
    const total = data.totalEndpoints || 0;
    const tested = data.testedEndpoints || 0;
    return {
      total: total * 3, // 3 test types per endpoint
      passed: tested * 3, // Approximate - assumes tested means all 3 types
      percentage: total > 0 ? Math.round((tested / total) * 100) : 0
    };
  };
  
  const coverage = calculateCoverage();
  const percentage = coverage.percentage;
  
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

  const handleRefresh = async (e) => {
    e.stopPropagation();
    if (onRefreshEndpoints && type === "controller") {
      setIsRefreshing(true);
      try {
        await onRefreshEndpoints(name, data);
      } finally {
        setIsRefreshing(false);
      }
    }
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
        
        {/* Refresh button for controller level */}
        {type === "controller" && onRefreshEndpoints && (
          <button
            onClick={handleRefresh}
            className="p-1 rounded hover:bg-muted transition-colors ml-2"
            title="TOAY listesini yenile"
          >
            <RefreshCw className={cn("w-3.5 h-3.5 text-muted-foreground hover:text-primary", isRefreshing && "animate-spin")} />
          </button>
        )}
        
        <Badge className={cn("ml-auto", getPercentageColor())}>
          {percentage}%
        </Badge>
        
        <span className="text-sm text-muted-foreground whitespace-nowrap">
          {type === "controller" 
            ? `${coverage.passed}/${coverage.total}` 
            : `${data.testedEndpoints || 0}/${data.totalEndpoints || 0} EP`
          }
        </span>
      </div>
      
      {isExpanded && hasChildren && (
        <div className="mt-1">
          {type === "project" && data.apps && Object.entries(data.apps).map(([appName, appData]) => (
            <TreeNode key={appName} name={appName} data={appData} level={level + 1} type="app" onRefreshEndpoints={onRefreshEndpoints} />
          ))}
          
          {type === "app" && data.controllers && Object.entries(data.controllers).map(([ctrlName, ctrlData]) => (
            <TreeNode key={ctrlName} name={ctrlName} data={ctrlData} level={level + 1} type="controller" onRefreshEndpoints={onRefreshEndpoints} />
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
  
  // Check if specific test types exist and are passed
  // Each endpoint MUST have at least 1 of each: Happy, Alternatif, Negatif
  // ONLY check testType field from Jira - DO NOT check test name
  
  const isHappyTest = (t) => {
    const testType = (t.testType || t.type || '').toLowerCase();
    return testType.includes('happy');
  };
  
  const isAlternatifTest = (t) => {
    const testType = (t.testType || t.type || '').toLowerCase();
    return testType.includes('alternatif') || testType.includes('alternative');
  };
  
  const isNegatifTest = (t) => {
    const testType = (t.testType || t.type || '').toLowerCase();
    return testType.includes('negatif') || testType.includes('negative');
  };
  
  const hasHappyPassed = endpoint.tests?.some(t => 
    isHappyTest(t) && t.status === 'PASSED'
  ) || endpoint.happy;
  
  const hasAlternatifPassed = endpoint.tests?.some(t => 
    isAlternatifTest(t) && t.status === 'PASSED'
  ) || endpoint.alternatif;
  
  const hasNegatifPassed = endpoint.tests?.some(t => 
    isNegatifTest(t) && t.status === 'PASSED'
  ) || endpoint.negatif;
  
  // Calculate coverage percentage based on 3 required test types
  const passedTypes = [hasHappyPassed, hasAlternatifPassed, hasNegatifPassed].filter(Boolean).length;
  const coveragePercent = Math.round((passedTypes / 3) * 100);
  
  // Determine if fully tested (all 3 types passed)
  const isFullyCovered = passedTypes === 3;
  
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
          {/* Coverage percentage based on 3 required test types */}
          <Badge className={cn(
            "text-xs",
            coveragePercent === 100 ? "bg-green-500" :
            coveragePercent >= 66 ? "bg-yellow-500" :
            coveragePercent >= 33 ? "bg-orange-500" : "bg-red-500"
          )}>
            {coveragePercent}%
          </Badge>
          
          <span className="text-xs text-muted-foreground">
            ({passedTypes}/3)
          </span>
          
          {/* Test Type Badges - Green for passed, Red for missing/not passed */}
          <Badge className={cn(
            "transition-colors text-xs",
            hasHappyPassed 
              ? "bg-green-500/20 text-green-400 border border-green-500/40" 
              : "bg-red-500/20 text-red-400 border border-red-500/40"
          )}>
            {hasHappyPassed ? "✅" : "❌"} HP
          </Badge>
          <Badge className={cn(
            "transition-colors text-xs",
            hasAlternatifPassed 
              ? "bg-green-500/20 text-green-400 border border-green-500/40" 
              : "bg-red-500/20 text-red-400 border border-red-500/40"
          )}>
            {hasAlternatifPassed ? "✅" : "❌"} AS
          </Badge>
          <Badge className={cn(
            "transition-colors text-xs",
            hasNegatifPassed 
              ? "bg-green-500/20 text-green-400 border border-green-500/40" 
              : "bg-red-500/20 text-red-400 border border-red-500/40"
          )}>
            {hasNegatifPassed ? "✅" : "❌"} NS
          </Badge>
        </div>
      </div>
      
      {/* Tests */}
      {isExpanded && hasTests && (
        <div className="ml-6 mt-1 space-y-1">
          {endpoint.tests.map((test, idx) => (
            <div
              key={idx}
              className={cn(
                "flex items-center gap-2 p-2 rounded border text-sm",
                test.status === "PASSED" 
                  ? "bg-green-500/10 border-green-500/30" 
                  : "bg-red-500/10 border-red-500/30"
              )}
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
