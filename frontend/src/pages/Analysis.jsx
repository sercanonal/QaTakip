import { useState, useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { ScrollArea } from "../components/ui/scroll-area";
import { toast } from "sonner";
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Filter,
  Search,
  Download,
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
  PieChart,
  MoreVertical,
  Play,
  Eye,
  Smartphone,
  Bot,
} from "lucide-react";
import { cn } from "../lib/utils";

const API_URL = process.env.REACT_APP_BACKEND_URL || "";

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 100,
    },
  },
};

// Platform detection helper
const detectPlatform = (cycleName) => {
  if (!cycleName) return null;
  const name = cycleName.toLowerCase();
  if (name.includes("ios") || name.includes("iphone") || name.includes("ipad")) {
    return { name: "iOS", icon: Smartphone, color: "text-blue-400" };
  }
  if (name.includes("android")) {
    return { name: "Android", icon: Bot, color: "text-green-400" };
  }
  return null;
};

const Analysis = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("test-analysis");
  
  // Test Analysis State
  const [projects, setProjects] = useState([]);
  const [selectedProjects, setSelectedProjects] = useState([]);
  const [analysisForm, setAnalysisForm] = useState({
    cycleStartsWith: "",
    cycleContains: "",
    cycleExcludes: "",
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
      const response = await api.get("/analysis/projects");
      setProjects(response.data.projects || []);
    } catch (error) {
      console.error("Error loading projects:", error);
      // Mock data for demo
      setProjects([
        { name: "MBAPAY", icon: "💰" },
        { name: "MBAINT", icon: "🏦" },
        { name: "MBAPOS", icon: "🖥️" },
        { name: "MBAMOB", icon: "📱" },
      ]);
    }
  };

  const handleAnalyze = async () => {
    if (selectedProjects.length === 0) {
      toast.error("En az bir proje seçin!");
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
          projectNames: selectedProjects,
          ...analysisForm,
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
      ? <ArrowUp className="w-4 h-4 text-primary" />
      : <ArrowDown className="w-4 h-4 text-primary" />;
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
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-500 via-cyan-500 to-teal-500 bg-clip-text text-transparent">
            Test Analizi
          </h1>
          <p className="text-muted-foreground mt-1">
            Cycle ve test durumlarını analiz edin
          </p>
        </div>
        <Badge variant="outline" className="animate-pulse">
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
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-cyan-500 data-[state=active]:text-white transition-all duration-300"
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              Test Analizi
            </TabsTrigger>
            <TabsTrigger 
              value="api-analysis"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-purple-500 data-[state=active]:to-pink-500 data-[state=active]:text-white transition-all duration-300"
            >
              <Target className="w-4 h-4 mr-2" />
              API Analizi
            </TabsTrigger>
          </TabsList>

          {/* TEST ANALYSIS TAB */}
          <TabsContent value="test-analysis" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Input Form */}
              <Card className="lg:col-span-1 bg-card/50 backdrop-blur border-blue-500/20 hover:border-blue-500/40 transition-all duration-300">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Filter className="w-5 h-5 text-blue-500" />
                    Analiz Parametreleri
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Project Selection */}
                  <div className="space-y-2">
                    <Label>Projeler</Label>
                    <div className="flex flex-wrap gap-2">
                      {projects.map((project) => (
                        <Button
                          key={project.name}
                          type="button"
                          variant={selectedProjects.includes(project.name) ? "default" : "outline"}
                          size="sm"
                          onClick={() => toggleProject(project.name)}
                          className={cn(
                            "transition-all duration-200",
                            selectedProjects.includes(project.name) && "bg-gradient-to-r from-blue-500 to-cyan-500"
                          )}
                        >
                          <span className="mr-1">{project.icon}</span>
                          {project.name}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Cycle Başlangıcı</Label>
                    <Input
                      placeholder="örn: REG_"
                      value={analysisForm.cycleStartsWith}
                      onChange={(e) => setAnalysisForm(prev => ({ ...prev, cycleStartsWith: e.target.value }))}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Cycle İçeriği</Label>
                    <Input
                      placeholder="örn: 2024"
                      value={analysisForm.cycleContains}
                      onChange={(e) => setAnalysisForm(prev => ({ ...prev, cycleContains: e.target.value }))}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Hariç Tut</Label>
                    <Input
                      placeholder="örn: OLD_"
                      value={analysisForm.cycleExcludes}
                      onChange={(e) => setAnalysisForm(prev => ({ ...prev, cycleExcludes: e.target.value }))}
                    />
                  </div>

                  <Button
                    onClick={handleAnalyze}
                    disabled={analysisLoading}
                    className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-500/90 hover:to-cyan-500/90"
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
                    className="h-[300px] rounded-lg bg-black/50 p-4 font-mono text-sm text-cyan-400"
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
                <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-muted-foreground">Toplam</p>
                        <p className="text-2xl font-bold text-blue-400">{analysisStats.total}</p>
                      </div>
                      <Layers className="w-8 h-8 text-blue-500/50" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-yellow-500/10 to-yellow-600/5 border-yellow-500/20">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-muted-foreground">Bakım Gerekli</p>
                        <p className="text-2xl font-bold text-yellow-400">{analysisStats.needMaintenance}</p>
                      </div>
                      <AlertTriangle className="w-8 h-8 text-yellow-500/50" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-muted-foreground">Pass (Reg.)</p>
                        <p className="text-2xl font-bold text-green-400">{analysisStats.passedInRegression}</p>
                      </div>
                      <CheckCircle2 className="w-8 h-8 text-green-500/50" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 border-emerald-500/20">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-muted-foreground">Pass (Non-Reg.)</p>
                        <p className="text-2xl font-bold text-emerald-400">{analysisStats.passedNotInRegression}</p>
                      </div>
                      <CheckCircle2 className="w-8 h-8 text-emerald-500/50" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-red-500/10 to-red-600/5 border-red-500/20">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-muted-foreground">Fail (Non-Reg.)</p>
                        <p className="text-2xl font-bold text-red-400">{analysisStats.failedNotInRegression}</p>
                      </div>
                      <XCircle className="w-8 h-8 text-red-500/50" />
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
                            className="pl-9 w-[200px]"
                          />
                        </div>
                        
                        <Select value={statusFilter} onValueChange={setStatusFilter}>
                          <SelectTrigger className="w-[130px]">
                            <SelectValue placeholder="Status" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="">Tümü</SelectItem>
                            <SelectItem value="Pass">Pass</SelectItem>
                            <SelectItem value="Fail">Fail</SelectItem>
                          </SelectContent>
                        </Select>

                        <Select value={regressionFilter} onValueChange={setRegressionFilter}>
                          <SelectTrigger className="w-[130px]">
                            <SelectValue placeholder="Regression" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="">Tümü</SelectItem>
                            <SelectItem value="true">Reg. Var</SelectItem>
                            <SelectItem value="false">Reg. Yok</SelectItem>
                          </SelectContent>
                        </Select>

                        <Select value={projectFilter} onValueChange={setProjectFilter}>
                          <SelectTrigger className="w-[130px]">
                            <SelectValue placeholder="Proje" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="">Tümü</SelectItem>
                            {selectedProjects.map(p => (
                              <SelectItem key={p} value={p}>{p}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>

                        <Button variant="outline" size="icon" onClick={resetFilters}>
                          <RefreshCw className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                    
                    {/* Action buttons */}
                    <div className="flex items-center gap-2 mt-4">
                      <Button variant="outline" size="sm" onClick={handleSelectAll}>
                        {selectedRows.length === sortedResults.length ? "Seçimi Kaldır" : "Tümünü Seç"}
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={copySelectedKeys}
                        disabled={selectedRows.length === 0}
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
                              const platform = detectPlatform(row.cycleName);
                              return (
                                <motion.tr
                                  key={row.key}
                                  initial={{ opacity: 0 }}
                                  animate={{ opacity: 1 }}
                                  exit={{ opacity: 0 }}
                                  transition={{ delay: idx * 0.01 }}
                                  className={cn(
                                    "hover:bg-secondary/50 transition-colors",
                                    selectedRows.includes(row.key) && "bg-primary/10"
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
                                      <Badge variant="outline" className={platform.color}>
                                        <platform.icon className="w-3 h-3 mr-1" />
                                        {platform.name}
                                      </Badge>
                                    )}
                                  </TableCell>
                                  <TableCell>
                                    <Badge variant={row.inRegression ? "default" : "secondary"}>
                                      {row.inRegression ? "✅ Var" : "❌ Yok"}
                                    </Badge>
                                  </TableCell>
                                  <TableCell>
                                    <Badge 
                                      variant={row.status === "Pass" ? "default" : "destructive"}
                                      className={row.status === "Pass" ? "bg-green-500" : ""}
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

          {/* API ANALYSIS TAB - Placeholder */}
          <TabsContent value="api-analysis" className="space-y-6">
            <Card className="bg-card/50 backdrop-blur border-purple-500/20">
              <CardContent className="p-12 text-center">
                <Target className="w-16 h-16 mx-auto text-purple-500/50 mb-4" />
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
