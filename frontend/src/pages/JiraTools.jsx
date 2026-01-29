import { useState, useRef, useEffect } from "react";
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
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import { ScrollArea } from "../components/ui/scroll-area";
import { toast } from "sonner";
import {
  Sparkles,
  Bug,
  Plus,
  Play,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Loader2,
  Copy,
  ChevronRight,
  FileJson,
  Link2,
  Zap,
  Target,
  Layers,
  GitBranch,
  Send,
  Edit3,
  ListPlus,
} from "lucide-react";
import { cn } from "../lib/utils";

const API_URL = process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_API_URL || "http://localhost:8001";

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

// Status bilgileri - Mor/Mavi tonlarında
const STATUS_INFO = {
  216: { name: "Not Executed", color: "bg-slate-500", textColor: "text-slate-400" },
  217: { name: "In Progress", color: "bg-amber-500", textColor: "text-amber-400" },
  218: { name: "Pass", color: "bg-emerald-500", textColor: "text-emerald-400" },
  219: { name: "Fail", color: "bg-rose-500", textColor: "text-rose-400" },
  220: { name: "Blocked", color: "bg-sky-500", textColor: "text-sky-400" },
  5116: { name: "Pass(Manuel)", color: "bg-teal-500", textColor: "text-teal-400" },
};

const JiraTools = () => {
  const [activeTab, setActiveTab] = useState("jiragen");
  
  // Cycles & Projects
  const [cycles, setCycles] = useState([]);
  const [projects, setProjects] = useState([]);
  
  // Jira Generator State
  const [jiraGenForm, setJiraGenForm] = useState({
    testType: "api",
    jsonData: "",
  });
  const [validatedTests, setValidatedTests] = useState([]);
  const [jiraGenStats, setJiraGenStats] = useState({ total: 0, valid: 0, invalid: 0 });
  const [jiraGenOutput, setJiraGenOutput] = useState("");
  const [jiraGenLoading, setJiraGenLoading] = useState(false);
  const [creatingTests, setCreatingTests] = useState(false);
  
  // Bug Bağla State (Çoklu - 2 cycle karşılaştırma)
  const [bugBaglaForm, setBugBaglaForm] = useState({
    currentCycleKey: "",
    baseCycleKey: "",
    statusIds: [219], // Default: Fail
  });
  const [bugBaglaResults, setBugBaglaResults] = useState(null);
  const [bugBaglaOutput, setBugBaglaOutput] = useState("");
  const [bugBaglaLoading, setBugBaglaLoading] = useState(false);
  const [bindingBugs, setBindingBugs] = useState(false);
  
  // Cycle Add State
  const [cycleAddForm, setCycleAddForm] = useState({
    cycleKey: "",
    addItems: "",
  });
  const [cycleAddResults, setCycleAddResults] = useState(null);
  const [cycleAddOutput, setCycleAddOutput] = useState("");
  const [cycleAddLoading, setCycleAddLoading] = useState(false);
  const [addingToCycle, setAddingToCycle] = useState(false);
  
  // API Rerun State
  const [apiRerunForm, setApiRerunForm] = useState({
    cycleName: "",
    projectNames: [],
    outputFormat: "jenkins",
  });
  const [apiRerunOutput, setApiRerunOutput] = useState("");
  const [apiRerunLoading, setApiRerunLoading] = useState(false);
  const [apiRerunResult, setApiRerunResult] = useState(null);
  
  const outputRef = useRef(null);

  // Load cycles and projects on mount
  useEffect(() => {
    loadCycles();
    loadProjects();
  }, []);

  // Auto-scroll output
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [jiraGenOutput, bugBaglaOutput, cycleAddOutput, apiRerunOutput]);

  const loadCycles = async () => {
    try {
      const response = await api.get("/cycles");
      setCycles(response.data.cycles || []);
    } catch (error) {
      console.error("Cycles yüklenemedi:", error);
    }
  };

  const loadProjects = async () => {
    try {
      const response = await api.get("/qa-projects");
      setProjects(response.data.projects || []);
    } catch (error) {
      console.error("Projeler yüklenemedi:", error);
    }
  };

  // ==================== JIRA GENERATOR ====================
  
  const handleJiraGenValidate = async () => {
    if (!jiraGenForm.jsonData.trim()) {
      toast.error("JSON verisi boş olamaz!");
      return;
    }

    setJiraGenLoading(true);
    setJiraGenOutput("");
    setValidatedTests([]);
    setJiraGenStats({ total: 0, valid: 0, invalid: 0 });

    try {
      const response = await fetch(`${API_URL}/api/jira-tools/jiragen/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          isUiTest: jiraGenForm.testType === "ui",
          jsonData: jiraGenForm.jsonData,
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
              if (data.log) setJiraGenOutput(prev => prev + data.log + "\n");
              if (data.complete && data.result) {
                setValidatedTests(data.result.tests);
                setJiraGenStats(data.result.stats);
                toast.success(`${data.result.stats.valid} geçerli test bulundu!`);
              }
              if (data.error) toast.error(data.error);
            } catch (e) { console.error("Parse error:", e); }
          }
        }
      }
    } catch (error) {
      toast.error("Bağlantı hatası: " + error.message);
    } finally {
      setJiraGenLoading(false);
    }
  };

  const handleCreateTest = async (test, index) => {
    setCreatingTests(true);
    try {
      const response = await fetch(`${API_URL}/api/jira-tools/jiragen/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          testData: test.rawTest,
          isUiTest: jiraGenForm.testType === "ui",
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
              if (data.complete && data.result) {
                if (data.result.success) {
                  toast.success(`Test oluşturuldu: ${data.result.key}`);
                  setValidatedTests(prev => 
                    prev.map((t, i) => i === index ? { ...t, created: true, jiraKey: data.result.key } : t)
                  );
                } else {
                  toast.error(`Test oluşturulamadı: ${data.result.error}`);
                }
              }
            } catch (e) { console.error("Parse error:", e); }
          }
        }
      }
    } catch (error) {
      toast.error("Test oluşturma hatası: " + error.message);
    } finally {
      setCreatingTests(false);
    }
  };

  const handleCreateAllTests = async () => {
    const validTests = validatedTests.filter(t => t.validation.isValid && !t.created);
    if (validTests.length === 0) {
      toast.warning("Oluşturulacak geçerli test yok!");
      return;
    }

    setCreatingTests(true);
    let successCount = 0;

    for (let i = 0; i < validTests.length; i++) {
      const test = validTests[i];
      const testIndex = validatedTests.indexOf(test);
      try {
        await handleCreateTest(test, testIndex);
        successCount++;
      } catch { /* continue */ }
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    toast.success(`${successCount} test oluşturuldu!`);
    setCreatingTests(false);
  };

  // ==================== BUG BAĞLA (Çoklu) ====================
  
  const handleBugBaglaAnalyze = async () => {
    if (!bugBaglaForm.currentCycleKey || !bugBaglaForm.baseCycleKey) {
      toast.error("Her iki cycle key de gerekli!");
      return;
    }

    if (bugBaglaForm.statusIds.length === 0) {
      toast.error("En az bir status seçin!");
      return;
    }

    setBugBaglaLoading(true);
    setBugBaglaOutput("");
    setBugBaglaResults(null);

    try {
      const response = await fetch(`${API_URL}/api/jira-tools/bugbagla/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(bugBaglaForm),
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
              if (data.log) setBugBaglaOutput(prev => prev + data.log + "\n");
              if (data.complete && data.result) {
                setBugBaglaResults(data.result);
                toast.success(`${data.result.stats.toBind} test bağlanmaya hazır!`);
              }
              if (data.error) toast.error(data.error);
            } catch (e) { console.error("Parse error:", e); }
          }
        }
      }
    } catch (error) {
      toast.error("Bağlantı hatası: " + error.message);
    } finally {
      setBugBaglaLoading(false);
    }
  };

  const handleBindBugs = async () => {
    if (!bugBaglaResults || bugBaglaResults.willBind.length === 0) {
      toast.error("Bağlanacak test yok!");
      return;
    }

    setBindingBugs(true);
    setBugBaglaOutput(prev => prev + "\n🚀 Buglar bağlanıyor...\n");

    try {
      const bindings = bugBaglaResults.willBind.map(item => ({
        testKey: item.testKey,
        testResultId: item.testResultId,
        bugIds: item.bugIds,
        cycleId: bugBaglaResults.cycleId,
      }));

      const response = await fetch(`${API_URL}/api/jira-tools/bugbagla/bind`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bindings }),
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
              if (data.log) setBugBaglaOutput(prev => prev + data.log + "\n");
              if (data.success) toast.success("Buglar başarıyla bağlandı!");
              if (data.error) toast.error(data.error);
            } catch (e) { console.error("Parse error:", e); }
          }
        }
      }
    } catch (error) {
      toast.error("Bağlama hatası: " + error.message);
    } finally {
      setBindingBugs(false);
    }
  };

  const toggleStatus = (statusId) => {
    setBugBaglaForm(prev => ({
      ...prev,
      statusIds: prev.statusIds.includes(statusId)
        ? prev.statusIds.filter(id => id !== statusId)
        : [...prev.statusIds, statusId],
    }));
  };

  // ==================== CYCLE ADD ====================
  
  const handleCycleAddAnalyze = async () => {
    if (!cycleAddForm.cycleKey || !cycleAddForm.addItems.trim()) {
      toast.error("Cycle Key ve test listesi gerekli!");
      return;
    }

    const items = cycleAddForm.addItems.split("\n").map(s => s.trim()).filter(s => s);
    if (items.length === 0) {
      toast.error("En az bir test key girin!");
      return;
    }

    setCycleAddLoading(true);
    setCycleAddOutput("");
    setCycleAddResults(null);

    try {
      const response = await fetch(`${API_URL}/api/jira-tools/cycleadd/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cycleKey: cycleAddForm.cycleKey,
          addItems: items,
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
              if (data.log) setCycleAddOutput(prev => prev + data.log + "\n");
              if (data.complete && data.result) {
                setCycleAddResults(data.result);
                toast.success(`${data.result.stats.toAdd} test eklenmeye hazır!`);
              }
              if (data.error) toast.error(data.error);
            } catch (e) { console.error("Parse error:", e); }
          }
        }
      }
    } catch (error) {
      toast.error("Bağlantı hatası: " + error.message);
    } finally {
      setCycleAddLoading(false);
    }
  };

  const handleCycleAddExecute = async () => {
    if (!cycleAddResults?.saveBody) {
      toast.error("Önce analiz yapın!");
      return;
    }

    setAddingToCycle(true);
    setCycleAddOutput(prev => prev + "\n🚀 Testler ekleniyor...\n");

    try {
      const response = await fetch(`${API_URL}/api/jira-tools/cycleadd/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ saveBody: cycleAddResults.saveBody }),
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
              if (data.log) setCycleAddOutput(prev => prev + data.log + "\n");
              if (data.success) toast.success(`${data.result.added} test eklendi!`);
              if (data.error) toast.error(data.error);
            } catch (e) { console.error("Parse error:", e); }
          }
        }
      }
    } catch (error) {
      toast.error("Ekleme hatası: " + error.message);
    } finally {
      setAddingToCycle(false);
    }
  };

  // ==================== API RERUN ====================
  
  const handleApiRerun = async () => {
    if (!apiRerunForm.cycleName) {
      toast.error("Cycle adı gerekli!");
      return;
    }

    setApiRerunLoading(true);
    setApiRerunOutput("");
    setApiRerunResult(null);

    try {
      const response = await fetch(`${API_URL}/api/jira-tools/apirerun`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(apiRerunForm),
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
              if (data.log) setApiRerunOutput(prev => prev + data.log + "\n");
              if (data.complete && data.result) {
                setApiRerunResult(data.result);
                toast.success("Rerun listesi hazır!");
              }
              if (data.error) toast.error(data.error);
            } catch (e) { console.error("Parse error:", e); }
          }
        }
      }
    } catch (error) {
      toast.error("Bağlantı hatası: " + error.message);
    } finally {
      setApiRerunLoading(false);
    }
  };

  const toggleProject = (projectName) => {
    setApiRerunForm(prev => ({
      ...prev,
      projectNames: prev.projectNames.includes(projectName)
        ? prev.projectNames.filter(p => p !== projectName)
        : [...prev.projectNames, projectName],
    }));
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Panoya kopyalandı!");
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
          <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-500 via-purple-500 to-fuchsia-500 bg-clip-text text-transparent">
            Jira Araçları
          </h1>
          <p className="text-muted-foreground mt-1">
            Test oluşturma, bug bağlama ve cycle yönetimi
          </p>
        </div>
        <Badge variant="outline" className="border-violet-500/50 text-violet-400">
          <Zap className="w-3 h-3 mr-1" />
          VPN Gerekli
        </Badge>
      </motion.div>

      {/* Main Content */}
      <motion.div variants={itemVariants}>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4 gap-2 bg-card/50 p-2 rounded-xl backdrop-blur">
            <TabsTrigger 
              value="jiragen" 
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-violet-600 data-[state=active]:to-purple-600 data-[state=active]:text-white transition-all duration-300"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Jira Generator
            </TabsTrigger>
            <TabsTrigger 
              value="bugbagla"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-fuchsia-600 data-[state=active]:to-pink-600 data-[state=active]:text-white transition-all duration-300"
            >
              <Bug className="w-4 h-4 mr-2" />
              Bug Bağla
            </TabsTrigger>
            <TabsTrigger 
              value="cycleadd"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-emerald-600 data-[state=active]:to-teal-600 data-[state=active]:text-white transition-all duration-300"
            >
              <ListPlus className="w-4 h-4 mr-2" />
              Cycle Add
            </TabsTrigger>
            <TabsTrigger 
              value="rerun"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-sky-600 data-[state=active]:to-cyan-600 data-[state=active]:text-white transition-all duration-300"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              API Rerun
            </TabsTrigger>
          </TabsList>

          {/* JIRA GENERATOR TAB */}
          <TabsContent value="jiragen" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="bg-card/50 backdrop-blur border-violet-500/20 hover:border-violet-500/40 transition-all duration-300">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileJson className="w-5 h-5 text-violet-500" />
                    Test Verisi
                  </CardTitle>
                  <CardDescription>JSON formatında test verilerini yapıştırın</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Test Tipi</Label>
                    <Select
                      value={jiraGenForm.testType}
                      onValueChange={(value) => setJiraGenForm(prev => ({ ...prev, testType: value }))}
                    >
                      <SelectTrigger className="border-violet-500/30 focus:border-violet-500">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="api">
                          <div className="flex items-center gap-2">
                            <Target className="w-4 h-4 text-violet-500" />
                            API Test
                          </div>
                        </SelectItem>
                        <SelectItem value="ui">
                          <div className="flex items-center gap-2">
                            <Layers className="w-4 h-4 text-fuchsia-500" />
                            UI Test
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>JSON Verisi</Label>
                    <Textarea
                      placeholder='[{"name": "Test Name", "objective": "...", ...}]'
                      value={jiraGenForm.jsonData}
                      onChange={(e) => setJiraGenForm(prev => ({ ...prev, jsonData: e.target.value }))}
                      className="min-h-[300px] font-mono text-sm bg-background/50 border-violet-500/30 focus:border-violet-500"
                    />
                  </div>

                  <Button
                    onClick={handleJiraGenValidate}
                    disabled={jiraGenLoading}
                    className="w-full bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700"
                  >
                    {jiraGenLoading ? (
                      <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Doğrulanıyor...</>
                    ) : (
                      <><Play className="w-4 h-4 mr-2" />Validate</>
                    )}
                  </Button>
                </CardContent>
              </Card>

              <Card className="bg-card/50 backdrop-blur border-purple-500/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ChevronRight className="w-5 h-5 text-purple-500" />
                    Çıktı
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[400px] rounded-lg bg-slate-950/50 p-4 font-mono text-sm text-purple-300 border border-purple-500/20">
                    <pre className="whitespace-pre-wrap">{jiraGenOutput || "Çıktı burada görünecek..."}</pre>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>

            {/* Stats Cards */}
            {jiraGenStats.total > 0 && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="bg-gradient-to-br from-violet-500/10 to-violet-600/5 border-violet-500/20">
                  <CardContent className="p-6 flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Toplam</p>
                      <p className="text-3xl font-bold text-violet-400">{jiraGenStats.total}</p>
                    </div>
                    <Layers className="w-10 h-10 text-violet-500/50" />
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 border-emerald-500/20">
                  <CardContent className="p-6 flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Geçerli</p>
                      <p className="text-3xl font-bold text-emerald-400">{jiraGenStats.valid}</p>
                    </div>
                    <CheckCircle2 className="w-10 h-10 text-emerald-500/50" />
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-rose-500/10 to-rose-600/5 border-rose-500/20">
                  <CardContent className="p-6 flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Hatalı</p>
                      <p className="text-3xl font-bold text-rose-400">{jiraGenStats.invalid}</p>
                    </div>
                    <XCircle className="w-10 h-10 text-rose-500/50" />
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Validated Tests */}
            {validatedTests.length > 0 && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Doğrulanan Testler</h3>
                  <Button onClick={handleCreateAllTests} disabled={creatingTests} className="bg-gradient-to-r from-emerald-600 to-teal-600">
                    {creatingTests ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Zap className="w-4 h-4 mr-2" />}
                    Tümünü Oluştur ({validatedTests.filter(t => t.validation.isValid && !t.created).length})
                  </Button>
                </div>

                <div className="space-y-3">
                  {validatedTests.slice(0, 10).map((test, index) => (
                    <Card key={index} className={cn(
                      "border transition-all duration-300",
                      test.validation.isValid ? "border-emerald-500/30 hover:border-emerald-500/50" : "border-rose-500/30",
                      test.created && "border-violet-500/50 bg-violet-500/5"
                    )}>
                      <CardContent className="p-4 flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant={test.validation.isValid ? "default" : "destructive"} className={test.validation.isValid ? "bg-emerald-600" : ""}>
                              {test.validation.isValid ? <CheckCircle2 className="w-3 h-3 mr-1" /> : <XCircle className="w-3 h-3 mr-1" />}
                              {test.validation.isValid ? "Geçerli" : "Hatalı"}
                            </Badge>
                            {test.created && (
                              <Badge variant="outline" className="text-violet-400 border-violet-400">
                                <Link2 className="w-3 h-3 mr-1" />{test.jiraKey}
                              </Badge>
                            )}
                          </div>
                          <h4 className="font-medium truncate max-w-md">{test.name}</h4>
                        </div>
                        {test.validation.isValid && !test.created && (
                          <Button onClick={() => handleCreateTest(test, index)} disabled={creatingTests} size="sm" className="bg-gradient-to-r from-violet-600 to-purple-600">
                            <Send className="w-4 h-4 mr-1" />Oluştur
                          </Button>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </motion.div>
            )}
          </TabsContent>

          {/* BUG BAĞLA TAB */}
          <TabsContent value="bugbagla" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="bg-card/50 backdrop-blur border-fuchsia-500/20 hover:border-fuchsia-500/40 transition-all duration-300">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Bug className="w-5 h-5 text-fuchsia-500" />
                    Bug Bağlama (Çoklu)
                  </CardTitle>
                  <CardDescription>Base cycle'daki bug'ları mevcut cycle'a bağlayın</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Mevcut Cycle Key</Label>
                      <Input
                        placeholder="PROJ-C123"
                        value={bugBaglaForm.currentCycleKey}
                        onChange={(e) => setBugBaglaForm(prev => ({ ...prev, currentCycleKey: e.target.value }))}
                        className="border-fuchsia-500/30 focus:border-fuchsia-500"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Base Cycle Key</Label>
                      <Input
                        placeholder="PROJ-C100"
                        value={bugBaglaForm.baseCycleKey}
                        onChange={(e) => setBugBaglaForm(prev => ({ ...prev, baseCycleKey: e.target.value }))}
                        className="border-fuchsia-500/30 focus:border-fuchsia-500"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Status Filtresi</Label>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(STATUS_INFO).map(([id, status]) => (
                        <Button
                          key={id}
                          type="button"
                          variant={bugBaglaForm.statusIds.includes(parseInt(id)) ? "default" : "outline"}
                          size="sm"
                          onClick={() => toggleStatus(parseInt(id))}
                          className={cn(
                            "transition-all duration-200",
                            bugBaglaForm.statusIds.includes(parseInt(id)) && status.color
                          )}
                        >
                          {status.name}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <Button onClick={handleBugBaglaAnalyze} disabled={bugBaglaLoading} className="w-full bg-gradient-to-r from-fuchsia-600 to-pink-600 hover:from-fuchsia-700 hover:to-pink-700">
                    {bugBaglaLoading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Analiz Ediliyor...</> : <><Play className="w-4 h-4 mr-2" />Analiz Et</>}
                  </Button>
                </CardContent>
              </Card>

              <Card className="bg-card/50 backdrop-blur border-pink-500/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ChevronRight className="w-5 h-5 text-pink-500" />
                    Çıktı
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[300px] rounded-lg bg-slate-950/50 p-4 font-mono text-sm text-pink-300 border border-pink-500/20">
                    <pre className="whitespace-pre-wrap">{bugBaglaOutput || "Çıktı burada görünecek..."}</pre>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>

            {/* Bug Bağla Results */}
            {bugBaglaResults && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card className="bg-gradient-to-br from-violet-500/10 to-violet-600/5 border-violet-500/20">
                    <CardContent className="p-6">
                      <p className="text-sm text-muted-foreground">Toplam Test</p>
                      <p className="text-3xl font-bold text-violet-400">{bugBaglaResults.stats.total}</p>
                    </CardContent>
                  </Card>
                  <Card className="bg-gradient-to-br from-fuchsia-500/10 to-fuchsia-600/5 border-fuchsia-500/20">
                    <CardContent className="p-6">
                      <p className="text-sm text-muted-foreground">Bağlanacak</p>
                      <p className="text-3xl font-bold text-fuchsia-400">{bugBaglaResults.stats.toBind}</p>
                    </CardContent>
                  </Card>
                </div>

                {bugBaglaResults.willBind.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>Bağlanacak Testler</span>
                        <Button onClick={handleBindBugs} disabled={bindingBugs} className="bg-gradient-to-r from-emerald-600 to-teal-600">
                          {bindingBugs ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Link2 className="w-4 h-4 mr-2" />}
                          Onayla ve Bağla
                        </Button>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Test Key</TableHead>
                            <TableHead>Test Adı</TableHead>
                            <TableHead>Buglar</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {bugBaglaResults.willBind.slice(0, 10).map((item, idx) => (
                            <TableRow key={idx}>
                              <TableCell className="font-medium">{item.testKey}</TableCell>
                              <TableCell className="max-w-[200px] truncate">{item.testName}</TableCell>
                              <TableCell>
                                <div className="flex flex-wrap gap-1">
                                  {item.bugKeys?.map((key, i) => (
                                    <Badge key={i} variant="outline" className="text-fuchsia-400 border-fuchsia-400">{key}</Badge>
                                  ))}
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>
                )}
              </motion.div>
            )}
          </TabsContent>

          {/* CYCLE ADD TAB */}
          <TabsContent value="cycleadd" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="bg-card/50 backdrop-blur border-emerald-500/20 hover:border-emerald-500/40 transition-all duration-300">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ListPlus className="w-5 h-5 text-emerald-500" />
                    Cycle'a Test Ekle
                  </CardTitle>
                  <CardDescription>Test key'lerini alt alta yazın</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Cycle Key</Label>
                    <Input
                      placeholder="PROJ-C123"
                      value={cycleAddForm.cycleKey}
                      onChange={(e) => setCycleAddForm(prev => ({ ...prev, cycleKey: e.target.value }))}
                      className="border-emerald-500/30 focus:border-emerald-500"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Test Key'leri (Her satıra bir tane)</Label>
                    <Textarea
                      placeholder="PROJ-T1&#10;PROJ-T2&#10;PROJ-T3"
                      value={cycleAddForm.addItems}
                      onChange={(e) => setCycleAddForm(prev => ({ ...prev, addItems: e.target.value }))}
                      className="min-h-[200px] font-mono text-sm bg-background/50 border-emerald-500/30 focus:border-emerald-500"
                    />
                  </div>

                  <Button onClick={handleCycleAddAnalyze} disabled={cycleAddLoading} className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700">
                    {cycleAddLoading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Analiz Ediliyor...</> : <><Play className="w-4 h-4 mr-2" />Analiz Et</>}
                  </Button>
                </CardContent>
              </Card>

              <Card className="bg-card/50 backdrop-blur border-teal-500/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ChevronRight className="w-5 h-5 text-teal-500" />
                    Çıktı
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[300px] rounded-lg bg-slate-950/50 p-4 font-mono text-sm text-teal-300 border border-teal-500/20">
                    <pre className="whitespace-pre-wrap">{cycleAddOutput || "Çıktı burada görünecek..."}</pre>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>

            {/* Cycle Add Results */}
            {cycleAddResults && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card className="bg-gradient-to-br from-violet-500/10 to-violet-600/5 border-violet-500/20">
                    <CardContent className="p-6">
                      <p className="text-sm text-muted-foreground">Toplam</p>
                      <p className="text-3xl font-bold text-violet-400">{cycleAddResults.stats.total}</p>
                    </CardContent>
                  </Card>
                  <Card className="bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 border-emerald-500/20">
                    <CardContent className="p-6">
                      <p className="text-sm text-muted-foreground">Eklenecek</p>
                      <p className="text-3xl font-bold text-emerald-400">{cycleAddResults.stats.toAdd}</p>
                    </CardContent>
                  </Card>
                  <Card className="bg-gradient-to-br from-amber-500/10 to-amber-600/5 border-amber-500/20">
                    <CardContent className="p-6">
                      <p className="text-sm text-muted-foreground">Atlanacak</p>
                      <p className="text-3xl font-bold text-amber-400">{cycleAddResults.stats.toSkip}</p>
                    </CardContent>
                  </Card>
                </div>

                {cycleAddResults.willBeAdded.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>Eklenecek Testler</span>
                        <Button onClick={handleCycleAddExecute} disabled={addingToCycle} className="bg-gradient-to-r from-emerald-600 to-teal-600">
                          {addingToCycle ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Plus className="w-4 h-4 mr-2" />}
                          Ekle ({cycleAddResults.willBeAdded.length})
                        </Button>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Test Key</TableHead>
                            <TableHead>Test Adı</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {cycleAddResults.willBeAdded.slice(0, 10).map((item, idx) => (
                            <TableRow key={idx}>
                              <TableCell className="font-medium">{item.key}</TableCell>
                              <TableCell className="max-w-[300px] truncate">{item.name}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>
                )}
              </motion.div>
            )}
          </TabsContent>

          {/* API RERUN TAB */}
          <TabsContent value="rerun" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="bg-card/50 backdrop-blur border-sky-500/20 hover:border-sky-500/40 transition-all duration-300">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <RefreshCw className="w-5 h-5 text-sky-500" />
                    API Rerun
                  </CardTitle>
                  <CardDescription>Fail olan API testlerini tekrar çalıştır</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Cycle Adı</Label>
                    <Input
                      placeholder="REG_Sprint_2024"
                      value={apiRerunForm.cycleName}
                      onChange={(e) => setApiRerunForm(prev => ({ ...prev, cycleName: e.target.value }))}
                      className="border-sky-500/30 focus:border-sky-500"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Projeler</Label>
                    <div className="flex flex-wrap gap-2">
                      {projects.map((project) => (
                        <Button
                          key={project.name}
                          type="button"
                          variant={apiRerunForm.projectNames.includes(project.name) ? "default" : "outline"}
                          size="sm"
                          onClick={() => toggleProject(project.name)}
                          className={cn(
                            "transition-all duration-200",
                            apiRerunForm.projectNames.includes(project.name) && "bg-gradient-to-r from-sky-600 to-cyan-600"
                          )}
                        >
                          <span className="mr-1">{project.icon}</span>
                          {project.name}
                        </Button>
                      ))}
                    </div>
                    {projects.length === 0 && (
                      <p className="text-sm text-muted-foreground">Proje yok. Ayarlardan proje ekleyin.</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label>Çıktı Formatı</Label>
                    <Select
                      value={apiRerunForm.outputFormat}
                      onValueChange={(value) => setApiRerunForm(prev => ({ ...prev, outputFormat: value }))}
                    >
                      <SelectTrigger className="border-sky-500/30 focus:border-sky-500">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="jenkins">Jenkins Format</SelectItem>
                        <SelectItem value="list">Liste Format</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Button onClick={handleApiRerun} disabled={apiRerunLoading} className="w-full bg-gradient-to-r from-sky-600 to-cyan-600 hover:from-sky-700 hover:to-cyan-700">
                    {apiRerunLoading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Çalışıyor...</> : <><Play className="w-4 h-4 mr-2" />Çalıştır</>}
                  </Button>
                </CardContent>
              </Card>

              <Card className="bg-card/50 backdrop-blur border-cyan-500/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ChevronRight className="w-5 h-5 text-cyan-500" />
                    Çıktı
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[300px] rounded-lg bg-slate-950/50 p-4 font-mono text-sm text-cyan-300 border border-cyan-500/20">
                    <pre className="whitespace-pre-wrap">{apiRerunOutput || "Çıktı burada görünecek..."}</pre>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>

            {/* API Rerun Results */}
            {apiRerunResult && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>Sonuç</span>
                      <Button onClick={() => copyToClipboard(apiRerunResult.output || "")} variant="outline" size="sm">
                        <Copy className="w-4 h-4 mr-1" />Kopyala
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-[200px] rounded-lg bg-slate-950/50 p-4 font-mono text-sm text-sky-300 border border-sky-500/20">
                      <pre className="whitespace-pre-wrap">{apiRerunResult.output || "Sonuç yok"}</pre>
                    </ScrollArea>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </TabsContent>
        </Tabs>
      </motion.div>
    </motion.div>
  );
};

export default JiraTools;
