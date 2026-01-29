import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import api from "../lib/api";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Checkbox } from "../components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { ScrollArea } from "../components/ui/scroll-area";
import { toast } from "sonner";
import {
  BarChart3,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Filter,
  Search,
  Copy,
  RefreshCw,
  Loader2,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ChevronRight,
  Layers,
  Target,
  Activity,
  Play,
  Smartphone,
  Bot,
  Globe,
} from "lucide-react";
import { cn } from "../lib/utils";

const API_URL = process.env.REACT_APP_BACKEND_URL || "";

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: "spring", stiffness: 100 },
  },
};

// Platform detection helper
const detectPlatform = (cycleName) => {
  if (!cycleName) return null;
  const name = cycleName.toLowerCase();
  if (name.includes("ios") || name.includes("iphone") || name.includes("ipad")) {
    return { name: "iOS", icon: Smartphone, color: "text-sky-400", bg: "bg-sky-500/10 border-sky-500/30" };
  }
  if (name.includes("android")) {
    return { name: "Android", icon: Bot, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/30" };
  }
  return { name: "Web", icon: Globe, color: "text-violet-400", bg: "bg-violet-500/10 border-violet-500/30" };
};

const Analysis = () => {
  const [activeTab, setActiveTab] = useState("test-analysis");
  
  // Projects (dinamik)
  const [projects, setProjects] = useState([]);
  const [selectedProjects, setSelectedProjects] = useState([]);
  
  // Test Analysis State
  const [analysisForm, setAnalysisForm] = useState({
    cycleId: "",
    days: "1",
    time: "00:00",
  });
  const [analysisResults, setAnalysisResults] = useState([]);
  const [analysisStats, setAnalysisStats] = useState({
    total: 0,
    needMaintenance: 0,
    passedInRegression: 0,
    passedNotInRegression: 0,
    failedNotInRegression: 0,
  });
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisOutput, setAnalysisOutput] = useState("");
  
  // API Analysis State
  const [apiForm, setApiForm] = useState({
    jiraTeamId: "",
    reportDate: new Date().toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric' }).replace(/\./g, '/'),
    days: "1",
    time: "00:00",
  });
  const [apiSelectedProjects, setApiSelectedProjects] = useState([]);
  const [apiResults, setApiResults] = useState([]);
  const [apiStats, setApiStats] = useState({
    total: 0, testedInReport: 0, notTestedInReport: 0, notInReport: 0,
    onlyInReport: 0, passed: 0, failed: 0, externalEndpoints: 0
  });
  const [apiMetrics, setApiMetrics] = useState({
    raporEndpointSayisi: 0, raporaYansiyanTest: 0, coverageOrani: "0",
    otomasyondaAmaRapordaYok: 0, passedAmaNegatifSayisi: 0,
    failedEtkilenenEndpointSayisi: 0, tahminiGuncelPass: 0, tahminiGuncelCoverage: "0"
  });
  const [apiLoading, setApiLoading] = useState(false);
  const [apiOutput, setApiOutput] = useState("");
  
  // API Filters
  const [apiSearchText, setApiSearchText] = useState("");
  const [apiStatusFilter, setApiStatusFilter] = useState("");
  const [apiRaporFilter, setApiRaporFilter] = useState("");
  const [apiExternalFilter, setApiExternalFilter] = useState("");
  
  // Filters
  const [searchText, setSearchText] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [regressionFilter, setRegressionFilter] = useState("");
  const [projectFilter, setProjectFilter] = useState("");
  
  // Sorting
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState("asc");
  
  // Selection
  const [selectedRows, setSelectedRows] = useState([]);
  
  const outputRef = useRef(null);
  const apiOutputRef = useRef(null);

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, []);

  // Auto-scroll output
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [analysisOutput]);

  const loadProjects = async () => {
    try {
      const response = await api.get("/qa-projects");
      setProjects(response.data.projects || []);
    } catch (error) {
      console.error("Projeler yüklenemedi:", error);
    }
  };

  const handleAnalyze = async () => {
    if (selectedProjects.length === 0) {
      toast.error("En az bir proje seçin!");
      return;
    }

    if (!analysisForm.cycleId) {
      toast.error("Cycle ID gerekli!");
      return;
    }

    setAnalysisLoading(true);
    setAnalysisOutput("");
    setAnalysisResults([]);
    setAnalysisStats({
      total: 0,
      needMaintenance: 0,
      passedInRegression: 0,
      passedNotInRegression: 0,
      failedNotInRegression: 0,
    });

    try {
      const response = await fetch(`${API_URL}/api/analysis/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cycleId: analysisForm.cycleId,
          days: parseInt(analysisForm.days) || 1,
          time: analysisForm.time || "00:00",
          projectNames: selectedProjects,
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.substring(6));
              
              if (data.log) {
                setAnalysisOutput(prev => prev + data.log + "\n");
              }
              
              if (data.success && data.tableData) {
                setAnalysisResults(data.tableData);
                setAnalysisStats(data.stats);
                toast.success(`${data.tableData.length} test analiz edildi!`);
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
      toast.error("Bağlantı hatası: " + error.message);
    } finally {
      setAnalysisLoading(false);
    }
  };

  // Filtering logic
  const filteredResults = analysisResults.filter(row => {
    const matchesSearch = !searchText || 
      row.key?.toLowerCase().includes(searchText.toLowerCase()) ||
      row.name?.toLowerCase().includes(searchText.toLowerCase());
    
    const matchesStatus = !statusFilter || row.status === statusFilter;
    const matchesRegression = !regressionFilter || 
      row.inRegression?.toString() === regressionFilter;
    const matchesProject = !projectFilter || row.project === projectFilter;
    
    return matchesSearch && matchesStatus && matchesRegression && matchesProject;
  });

  // Sorting logic
  const sortedResults = [...filteredResults].sort((a, b) => {
    if (!sortColumn) return 0;
    
    let aVal = a[sortColumn];
    let bVal = b[sortColumn];
    
    if (typeof aVal === "boolean") {
      aVal = aVal ? 1 : 0;
      bVal = bVal ? 1 : 0;
    }
    
    if (typeof aVal === "string") {
      aVal = aVal.toLowerCase();
      bVal = bVal.toLowerCase();
    }
    
    if (sortDirection === "asc") {
      return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
    } else {
      return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
    }
  });

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(prev => prev === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  };

  const handleSelectAll = () => {
    if (selectedRows.length === sortedResults.length) {
      setSelectedRows([]);
    } else {
      setSelectedRows(sortedResults.map(r => r.key));
    }
  };

  const handleSelectRow = (key) => {
    setSelectedRows(prev => 
      prev.includes(key) 
        ? prev.filter(k => k !== key)
        : [...prev, key]
    );
  };

  const copySelectedKeys = () => {
    if (selectedRows.length === 0) {
      toast.warning("Kopyalanacak satır seçin!");
      return;
    }
    
    navigator.clipboard.writeText(selectedRows.join("\n"));
    toast.success(`${selectedRows.length} key kopyalandı!`);
  };

  const resetFilters = () => {
    setSearchText("");
    setStatusFilter("");
    setRegressionFilter("");
    setProjectFilter("");
  };

  const toggleProject = (projectName) => {
    setSelectedProjects(prev =>
      prev.includes(projectName)
        ? prev.filter(p => p !== projectName)
        : [...prev, projectName]
    );
  };

  const SortIcon = ({ column }) => {
    if (sortColumn !== column) return <ArrowUpDown className="w-4 h-4 text-muted-foreground" />;
    return sortDirection === "asc" 
      ? <ArrowUp className="w-4 h-4 text-violet-400" />
      : <ArrowDown className="w-4 h-4 text-violet-400" />;
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-sky-500 via-cyan-500 to-teal-500 bg-clip-text text-transparent">
            Test Analizi
          </h1>
          <p className="text-muted-foreground mt-1">
            Cycle ve test durumlarını analiz edin
          </p>
        </div>
        <Badge variant="outline" className="border-sky-500/50 text-sky-400">
          <Activity className="w-3 h-3 mr-1" />
          VPN Gerekli
        </Badge>
      </motion.div>

      {/* Main Content */}
      <motion.div variants={itemVariants}>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 gap-2 bg-card/50 p-2 rounded-xl backdrop-blur">
            <TabsTrigger 
              value="test-analysis"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-sky-600 data-[state=active]:to-cyan-600 data-[state=active]:text-white transition-all duration-300"
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              Test Analizi
            </TabsTrigger>
            <TabsTrigger 
              value="api-analysis"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-violet-600 data-[state=active]:to-purple-600 data-[state=active]:text-white transition-all duration-300"
            >
              <Target className="w-4 h-4 mr-2" />
              API Analizi
            </TabsTrigger>
          </TabsList>

          {/* TEST ANALYSIS TAB */}
          <TabsContent value="test-analysis" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Input Form */}
              <Card className="lg:col-span-1 bg-card/50 backdrop-blur border-sky-500/20 hover:border-sky-500/40 transition-all duration-300">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Filter className="w-5 h-5 text-sky-500" />
                    Analiz Parametreleri
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Project Selection - Dinamik */}
                  <div className="space-y-2">
                    <Label>Projeler</Label>
                    <div className="flex flex-wrap gap-2">
                      {projects.length > 0 ? (
                        projects.map((project) => (
                          <Button
                            key={project.name}
                            type="button"
                            variant={selectedProjects.includes(project.name) ? "default" : "outline"}
                            size="sm"
                            onClick={() => toggleProject(project.name)}
                            className={cn(
                              "transition-all duration-200",
                              selectedProjects.includes(project.name) && "bg-gradient-to-r from-sky-600 to-cyan-600"
                            )}
                          >
                            <span className="mr-1">{project.icon}</span>
                            {project.name}
                          </Button>
                        ))
                      ) : (
                        <p className="text-sm text-muted-foreground">
                          Proje yok. Ayarlardan proje ekleyin.
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Cycle ID / Key</Label>
                    <Input
                      placeholder="PROJ-C123 veya cycle adı"
                      value={analysisForm.cycleId}
                      onChange={(e) => setAnalysisForm(prev => ({ ...prev, cycleId: e.target.value }))}
                      className="border-sky-500/30 focus:border-sky-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Kaç Gün</Label>
                      <Input
                        type="number"
                        min="0"
                        placeholder="1"
                        value={analysisForm.days}
                        onChange={(e) => setAnalysisForm(prev => ({ ...prev, days: e.target.value }))}
                        className="border-sky-500/30 focus:border-sky-500"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Saat</Label>
                      <Input
                        type="time"
                        value={analysisForm.time}
                        onChange={(e) => setAnalysisForm(prev => ({ ...prev, time: e.target.value }))}
                        className="border-sky-500/30 focus:border-sky-500"
                      />
                    </div>
                  </div>

                  <Button
                    onClick={handleAnalyze}
                    disabled={analysisLoading}
                    className="w-full bg-gradient-to-r from-sky-600 to-cyan-600 hover:from-sky-700 hover:to-cyan-700"
                  >
                    {analysisLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Analiz Ediliyor...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 mr-2" />
                        Analiz Başlat
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Output Console */}
              <Card className="lg:col-span-2 bg-card/50 backdrop-blur border-cyan-500/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ChevronRight className="w-5 h-5 text-cyan-500" />
                    Çıktı
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea 
                    ref={outputRef}
                    className="h-[300px] rounded-lg bg-slate-950/50 p-4 font-mono text-sm text-cyan-300 border border-cyan-500/20"
                  >
                    <pre className="whitespace-pre-wrap">
                      {analysisOutput || "Çıktı burada görünecek..."}
                    </pre>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>

            {/* Stats Cards */}
            {analysisStats.total > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="grid grid-cols-2 md:grid-cols-5 gap-4"
              >
                <Card className="bg-gradient-to-br from-violet-500/10 to-violet-600/5 border-violet-500/20">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-muted-foreground">Toplam</p>
                        <p className="text-2xl font-bold text-violet-400">{analysisStats.total}</p>
                      </div>
                      <Layers className="w-8 h-8 text-violet-500/50" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-amber-500/10 to-amber-600/5 border-amber-500/20">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-muted-foreground">Bakım Gerekli</p>
                        <p className="text-2xl font-bold text-amber-400">{analysisStats.needMaintenance}</p>
                      </div>
                      <AlertTriangle className="w-8 h-8 text-amber-500/50" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 border-emerald-500/20">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-muted-foreground">Pass (Reg.)</p>
                        <p className="text-2xl font-bold text-emerald-400">{analysisStats.passedInRegression}</p>
                      </div>
                      <CheckCircle2 className="w-8 h-8 text-emerald-500/50" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-teal-500/10 to-teal-600/5 border-teal-500/20">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-muted-foreground">Pass (Non-Reg.)</p>
                        <p className="text-2xl font-bold text-teal-400">{analysisStats.passedNotInRegression}</p>
                      </div>
                      <CheckCircle2 className="w-8 h-8 text-teal-500/50" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-rose-500/10 to-rose-600/5 border-rose-500/20">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-muted-foreground">Fail (Non-Reg.)</p>
                        <p className="text-2xl font-bold text-rose-400">{analysisStats.failedNotInRegression}</p>
                      </div>
                      <XCircle className="w-8 h-8 text-rose-500/50" />
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Results Table */}
            {analysisResults.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between flex-wrap gap-4">
                      <CardTitle>Sonuçlar ({sortedResults.length})</CardTitle>
                      
                      {/* Filters */}
                      <div className="flex items-center gap-2 flex-wrap">
                        <div className="relative">
                          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                          <Input
                            placeholder="Ara..."
                            value={searchText}
                            onChange={(e) => setSearchText(e.target.value)}
                            className="pl-9 w-[200px] border-violet-500/30"
                          />
                        </div>
                        
                        <Select value={statusFilter} onValueChange={setStatusFilter}>
                          <SelectTrigger className="w-[130px] border-violet-500/30">
                            <SelectValue placeholder="Status" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="">Tümü</SelectItem>
                            <SelectItem value="Pass">Pass</SelectItem>
                            <SelectItem value="Fail">Fail</SelectItem>
                          </SelectContent>
                        </Select>

                        <Select value={regressionFilter} onValueChange={setRegressionFilter}>
                          <SelectTrigger className="w-[130px] border-violet-500/30">
                            <SelectValue placeholder="Regression" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="">Tümü</SelectItem>
                            <SelectItem value="true">Reg. Var</SelectItem>
                            <SelectItem value="false">Reg. Yok</SelectItem>
                          </SelectContent>
                        </Select>

                        <Select value={projectFilter} onValueChange={setProjectFilter}>
                          <SelectTrigger className="w-[130px] border-violet-500/30">
                            <SelectValue placeholder="Proje" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="">Tümü</SelectItem>
                            {selectedProjects.map(p => (
                              <SelectItem key={p} value={p}>{p}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        <Button variant="outline" size="icon" onClick={resetFilters} className="border-violet-500/30">
                          <RefreshCw className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                    
                    {/* Action buttons */}
                    <div className="flex items-center gap-2 mt-4">
                      <Button variant="outline" size="sm" onClick={handleSelectAll} className="border-violet-500/30">
                        {selectedRows.length === sortedResults.length ? "Seçimi Kaldır" : "Tümünü Seç"}
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={copySelectedKeys}
                        disabled={selectedRows.length === 0}
                        className="border-violet-500/30"
                      >
                        <Copy className="w-4 h-4 mr-1" />
                        Kopyala ({selectedRows.length})
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-[500px]">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="w-12">
                              <Checkbox 
                                checked={selectedRows.length === sortedResults.length && sortedResults.length > 0}
                                onCheckedChange={handleSelectAll}
                              />
                            </TableHead>
                            <TableHead 
                              className="cursor-pointer hover:text-foreground transition-colors"
                              onClick={() => handleSort("key")}
                            >
                              <div className="flex items-center gap-1">
                                Key <SortIcon column="key" />
                              </div>
                            </TableHead>
                            <TableHead 
                              className="cursor-pointer hover:text-foreground transition-colors"
                              onClick={() => handleSort("name")}
                            >
                              <div className="flex items-center gap-1">
                                Test Adı <SortIcon column="name" />
                              </div>
                            </TableHead>
                            <TableHead 
                              className="cursor-pointer hover:text-foreground transition-colors"
                              onClick={() => handleSort("project")}
                            >
                              <div className="flex items-center gap-1">
                                Proje <SortIcon column="project" />
                              </div>
                            </TableHead>
                            <TableHead>Platform</TableHead>
                            <TableHead 
                              className="cursor-pointer hover:text-foreground transition-colors"
                              onClick={() => handleSort("inRegression")}
                            >
                              <div className="flex items-center gap-1">
                                Regression <SortIcon column="inRegression" />
                              </div>
                            </TableHead>
                            <TableHead 
                              className="cursor-pointer hover:text-foreground transition-colors"
                              onClick={() => handleSort("status")}
                            >
                              <div className="flex items-center gap-1">
                                Status <SortIcon column="status" />
                              </div>
                            </TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          <AnimatePresence>
                            {sortedResults.map((row, idx) => {
                              const platform = detectPlatform(row.name || row.cycleName);
                              return (
                                <motion.tr
                                  key={row.key}
                                  initial={{ opacity: 0 }}
                                  animate={{ opacity: 1 }}
                                  exit={{ opacity: 0 }}
                                  transition={{ delay: idx * 0.01 }}
                                  className={cn(
                                    "hover:bg-secondary/50 transition-colors",
                                    selectedRows.includes(row.key) && "bg-violet-500/10"
                                  )}
                                >
                                  <TableCell>
                                    <Checkbox 
                                      checked={selectedRows.includes(row.key)}
                                      onCheckedChange={() => handleSelectRow(row.key)}
                                    />
                                  </TableCell>
                                  <TableCell className="font-mono text-sm">{row.key}</TableCell>
                                  <TableCell className="max-w-[300px] truncate" title={row.name}>
                                    {row.name}
                                  </TableCell>
                                  <TableCell>{row.project}</TableCell>
                                  <TableCell>
                                    {platform && (
                                      <Badge variant="outline" className={cn(platform.color, platform.bg)}>
                                        <platform.icon className="w-3 h-3 mr-1" />
                                        {platform.name}
                                      </Badge>
                                    )}
                                  </TableCell>
                                  <TableCell>
                                    <Badge variant={row.inRegression ? "default" : "secondary"} className={row.inRegression ? "bg-emerald-600" : ""}>
                                      {row.inRegression ? "✓ Var" : "✗ Yok"}
                                    </Badge>
                                  </TableCell>
                                  <TableCell>
                                    <Badge 
                                      variant={row.status === "Pass" ? "default" : "destructive"}
                                      className={row.status === "Pass" ? "bg-emerald-600" : "bg-rose-600"}
                                    >
                                      {row.status === "Pass" ? (
                                        <CheckCircle2 className="w-3 h-3 mr-1" />
                                      ) : (
                                        <XCircle className="w-3 h-3 mr-1" />
                                      )}
                                      {row.status}
                                    </Badge>
                                  </TableCell>
                                </motion.tr>
                              );
                            })}
                          </AnimatePresence>
                        </TableBody>
                      </Table>
                    </ScrollArea>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </TabsContent>

          {/* API ANALYSIS TAB */}
          <TabsContent value="api-analysis" className="space-y-6">
            <Card className="bg-card/50 backdrop-blur border-violet-500/20">
              <CardContent className="p-12 text-center">
                <Target className="w-16 h-16 mx-auto text-violet-500/50 mb-4" />
                <h3 className="text-xl font-semibold mb-2">API Analizi</h3>
                <p className="text-muted-foreground">
                  API test analizi özelliği yakında eklenecek
                </p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </motion.div>
  );
};

export default Analysis;
