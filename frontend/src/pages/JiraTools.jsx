import { useState, useRef, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { motion, AnimatePresence } from "framer-motion";
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
  AlertCircle,
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
  Save,
  Trash2,
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

// Status bilgileri
const STATUS_INFO = {
  216: { name: "Not Executed", color: "bg-gray-500", icon: "⚪" },
  217: { name: "In Progress", color: "bg-orange-500", icon: "🟠" },
  218: { name: "Pass", color: "bg-green-500", icon: "🟢" },
  219: { name: "Fail", color: "bg-red-500", icon: "🔴" },
  220: { name: "Blocked", color: "bg-blue-500", icon: "🔵" },
  5116: { name: "Pass(Manuel)", color: "bg-emerald-600", icon: "🟢" },
};

// Scenario Types
const SCENARIO_TYPES = {
  812: { name: "Happy Path", color: "text-green-400", icon: "✅" },
  813: { name: "Alternatif Senaryo", color: "text-blue-400", icon: "🔀" },
  837: { name: "Negatif Senaryo", color: "text-red-400", icon: "❌" },
};

const JiraTools = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("jiragen");
  
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
  const [editingTestIndex, setEditingTestIndex] = useState(null);
  
  // Bug Bağla State
  const [bugBaglaForm, setBugBaglaForm] = useState({
    cycleKey: "",
    bugKey: "",
    statusIds: [219], // Default: Fail
  });
  const [bugBaglaResults, setBugBaglaResults] = useState(null);
  const [bugBaglaOutput, setBugBaglaOutput] = useState("");
  const [bugBaglaLoading, setBugBaglaLoading] = useState(false);
  const [bindingBugs, setBindingBugs] = useState(false);
  
  const outputRef = useRef(null);

  // Auto-scroll output
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [jiraGenOutput, bugBaglaOutput]);

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
              
              if (data.log) {
                setJiraGenOutput(prev => prev + data.log + "\n");
              }
              
              if (data.complete && data.result) {
                setValidatedTests(data.result.tests);
                setJiraGenStats(data.result.stats);
                toast.success(`${data.result.stats.valid} geçerli test bulundu!`);
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
                  // Update test status
                  setValidatedTests(prev => 
                    prev.map((t, i) => 
                      i === index ? { ...t, created: true, jiraKey: data.result.key } : t
                    )
                  );
                } else {
                  toast.error(`Test oluşturulamadı: ${data.result.error}`);
                }
              }
            } catch (e) {
              console.error("Parse error:", e);
            }
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
    let failCount = 0;

    for (let i = 0; i < validTests.length; i++) {
      const test = validTests[i];
      const testIndex = validatedTests.indexOf(test);
      
      try {
        await handleCreateTest(test, testIndex);
        successCount++;
      } catch {
        failCount++;
      }
      
      // Small delay between requests
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    toast.success(`Tamamlandı: ${successCount} başarılı, ${failCount} başarısız`);
    setCreatingTests(false);
  };

  // ==================== BUG BAĞLA ====================
  
  const handleBugBaglaAnalyze = async () => {
    if (!bugBaglaForm.cycleKey || !bugBaglaForm.bugKey) {
      toast.error("Cycle Key ve Bug Key gerekli!");
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
              
              if (data.log) {
                setBugBaglaOutput(prev => prev + data.log + "\n");
              }
              
              if (data.complete && data.result) {
                setBugBaglaResults(data.result);
                toast.success(`${data.result.stats.toBind} test bağlanmaya hazır!`);
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
      setBugBaglaLoading(false);
    }
  };

  const handleBindBugs = async () => {
    if (!bugBaglaResults || bugBaglaResults.candidates.length === 0) {
      toast.error("Bağlanacak test yok!");
      return;
    }

    setBindingBugs(true);
    setBugBaglaOutput(prev => prev + "\n🚀 Bug bağlanıyor...\n");

    try {
      const response = await fetch(`${API_URL}/api/jira-tools/bugbagla/bind`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bugId: bugBaglaResults.bugId,
          testResults: bugBaglaResults.candidates.map(c => c.testResultId),
          cycleId: bugBaglaResults.cycleId,
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
                setBugBaglaOutput(prev => prev + data.log + "\n");
              }
              
              if (data.success) {
                toast.success("Bug başarıyla bağlandı!");
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
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary via-purple-500 to-blue-500 bg-clip-text text-transparent">
            Jira Araçları
          </h1>
          <p className="text-muted-foreground mt-1">
            Test oluşturma, bug bağlama ve cycle yönetimi
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="animate-pulse">
            <Zap className="w-3 h-3 mr-1" />
            VPN Gerekli
          </Badge>
        </div>
      </motion.div>

      {/* Main Content */}
      <motion.div variants={itemVariants}>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4 gap-2 bg-card/50 p-2 rounded-xl backdrop-blur">
            <TabsTrigger 
              value="jiragen" 
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-purple-600 data-[state=active]:text-white transition-all duration-300"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Jira Generator
            </TabsTrigger>
            <TabsTrigger 
              value="bugbagla"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-red-500 data-[state=active]:to-orange-500 data-[state=active]:text-white transition-all duration-300"
            >
              <Bug className="w-4 h-4 mr-2" />
              Bug Bağla
            </TabsTrigger>
            <TabsTrigger 
              value="cycleadd"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-green-500 data-[state=active]:to-emerald-500 data-[state=active]:text-white transition-all duration-300"
            >
              <Plus className="w-4 h-4 mr-2" />
              Cycle Add
            </TabsTrigger>
            <TabsTrigger 
              value="rerun"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-cyan-500 data-[state=active]:text-white transition-all duration-300"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              API Rerun
            </TabsTrigger>
          </TabsList>

          {/* JIRA GENERATOR TAB */}
          <TabsContent value="jiragen" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Input Form */}
              <Card className="bg-card/50 backdrop-blur border-primary/20 hover:border-primary/40 transition-all duration-300">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileJson className="w-5 h-5 text-primary" />
                    Test Verisi
                  </CardTitle>
                  <CardDescription>
                    JSON formatında test verilerini yapıştırın
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Test Tipi</Label>
                    <Select
                      value={jiraGenForm.testType}
                      onValueChange={(value) => setJiraGenForm(prev => ({ ...prev, testType: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="api">
                          <div className="flex items-center gap-2">
                            <Target className="w-4 h-4" />
                            API Test
                          </div>
                        </SelectItem>
                        <SelectItem value="ui">
                          <div className="flex items-center gap-2">
                            <Layers className="w-4 h-4" />
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
                      className="min-h-[300px] font-mono text-sm bg-background/50"
                    />
                  </div>

                  <Button
                    onClick={handleJiraGenValidate}
                    disabled={jiraGenLoading}
                    className="w-full bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90"
                  >
                    {jiraGenLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Doğrulanıyor...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 mr-2" />
                        Validate
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Output Console */}
              <Card className="bg-card/50 backdrop-blur border-green-500/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ChevronRight className="w-5 h-5 text-green-500" />
                    Çıktı
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea 
                    ref={outputRef}
                    className="h-[400px] rounded-lg bg-black/50 p-4 font-mono text-sm text-green-400"
                  >
                    <pre className="whitespace-pre-wrap">
                      {jiraGenOutput || "Çıktı burada görünecek..."}
                    </pre>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>

            {/* Stats Cards */}
            {jiraGenStats.total > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="grid grid-cols-1 md:grid-cols-3 gap-4"
              >
                <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
                  <CardContent className="p-6 flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Toplam</p>
                      <p className="text-3xl font-bold text-blue-400">{jiraGenStats.total}</p>
                    </div>
                    <Layers className="w-10 h-10 text-blue-500/50" />
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
                  <CardContent className="p-6 flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Geçerli</p>
                      <p className="text-3xl font-bold text-green-400">{jiraGenStats.valid}</p>
                    </div>
                    <CheckCircle2 className="w-10 h-10 text-green-500/50" />
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-red-500/10 to-red-600/5 border-red-500/20">
                  <CardContent className="p-6 flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Hatalı</p>
                      <p className="text-3xl font-bold text-red-400">{jiraGenStats.invalid}</p>
                    </div>
                    <XCircle className="w-10 h-10 text-red-500/50" />
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Validated Tests List */}
            {validatedTests.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Doğrulanan Testler</h3>
                  <Button
                    onClick={handleCreateAllTests}
                    disabled={creatingTests}
                    className="bg-gradient-to-r from-green-500 to-emerald-500"
                  >
                    {creatingTests ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Zap className="w-4 h-4 mr-2" />
                    )}
                    Tümünü Oluştur ({validatedTests.filter(t => t.validation.isValid && !t.created).length})
                  </Button>
                </div>

                <div className="space-y-4">
                  <AnimatePresence>
                    {validatedTests.map((test, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <Card className={cn(
                          "border-2 transition-all duration-300",
                          test.validation.isValid 
                            ? "border-green-500/30 hover:border-green-500/50" 
                            : "border-red-500/30 hover:border-red-500/50",
                          test.created && "border-primary/50 bg-primary/5"
                        )}>
                          <CardContent className="p-4">
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1 space-y-2">
                                <div className="flex items-center gap-2">
                                  <Badge variant={test.validation.isValid ? "default" : "destructive"}>
                                    {test.validation.isValid ? (
                                      <CheckCircle2 className="w-3 h-3 mr-1" />
                                    ) : (
                                      <XCircle className="w-3 h-3 mr-1" />
                                    )}
                                    {test.validation.isValid ? "Geçerli" : "Hatalı"}
                                  </Badge>
                                  {test.created && (
                                    <Badge variant="outline" className="text-primary border-primary">
                                      <Link2 className="w-3 h-3 mr-1" />
                                      {test.jiraKey}
                                    </Badge>
                                  )}
                                  <span className="text-sm text-muted-foreground">
                                    Test #{test.index}
                                  </span>
                                </div>
                                <h4 className="font-medium">{test.name}</h4>
                                {test.rawTest.objective && (
                                  <p className="text-sm text-muted-foreground line-clamp-2">
                                    {test.rawTest.objective}
                                  </p>
                                )}
                                
                                {/* Validation Errors */}
                                {!test.validation.isValid && test.validation.errors.length > 0 && (
                                  <div className="mt-2 p-2 bg-red-500/10 rounded-lg">
                                    <p className="text-sm font-medium text-red-400 mb-1">Hatalar:</p>
                                    <ul className="list-disc list-inside text-xs text-red-300">
                                      {test.validation.errors.map((error, i) => (
                                        <li key={i}>{error}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}

                                {/* Steps preview */}
                                {test.steps && test.steps.length > 0 && (
                                  <div className="text-xs text-muted-foreground">
                                    {test.steps.length} adım
                                  </div>
                                )}
                              </div>

                              <div className="flex items-center gap-2">
                                <Dialog>
                                  <DialogTrigger asChild>
                                    <Button variant="outline" size="sm">
                                      <Edit3 className="w-4 h-4" />
                                    </Button>
                                  </DialogTrigger>
                                  <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
                                    <DialogHeader>
                                      <DialogTitle>Test Düzenle</DialogTitle>
                                      <DialogDescription>
                                        Test #{test.index}: {test.name}
                                      </DialogDescription>
                                    </DialogHeader>
                                    <div className="space-y-4 mt-4">
                                      <div className="space-y-2">
                                        <Label>Test Adı</Label>
                                        <Input defaultValue={test.name} />
                                      </div>
                                      <div className="space-y-2">
                                        <Label>Objective</Label>
                                        <Textarea defaultValue={test.rawTest.objective} />
                                      </div>
                                      <div className="space-y-2">
                                        <Label>Precondition</Label>
                                        <Textarea defaultValue={test.rawTest.precondition} />
                                      </div>
                                      {test.steps && test.steps.length > 0 && (
                                        <div className="space-y-2">
                                          <Label>Steps ({test.steps.length})</Label>
                                          <Table>
                                            <TableHeader>
                                              <TableRow>
                                                <TableHead className="w-12">#</TableHead>
                                                <TableHead>Description</TableHead>
                                                <TableHead>Test Data</TableHead>
                                                <TableHead>Expected Result</TableHead>
                                              </TableRow>
                                            </TableHeader>
                                            <TableBody>
                                              {test.steps.map((step, stepIdx) => (
                                                <TableRow key={stepIdx}>
                                                  <TableCell>{step.index}</TableCell>
                                                  <TableCell className="text-xs">{step.description}</TableCell>
                                                  <TableCell className="text-xs">{step.testData}</TableCell>
                                                  <TableCell className="text-xs">{step.expectedResult}</TableCell>
                                                </TableRow>
                                              ))}
                                            </TableBody>
                                          </Table>
                                        </div>
                                      )}
                                    </div>
                                  </DialogContent>
                                </Dialog>
                                
                                {test.validation.isValid && !test.created && (
                                  <Button
                                    onClick={() => handleCreateTest(test, index)}
                                    disabled={creatingTests}
                                    size="sm"
                                    className="bg-gradient-to-r from-green-500 to-emerald-500"
                                  >
                                    {creatingTests ? (
                                      <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                      <>
                                        <Send className="w-4 h-4 mr-1" />
                                        Oluştur
                                      </>
                                    )}
                                  </Button>
                                )}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </motion.div>
            )}
          </TabsContent>

          {/* BUG BAĞLA TAB */}
          <TabsContent value="bugbagla" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Input Form */}
              <Card className="bg-card/50 backdrop-blur border-red-500/20 hover:border-red-500/40 transition-all duration-300">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Bug className="w-5 h-5 text-red-500" />
                    Bug Bağlama
                  </CardTitle>
                  <CardDescription>
                    Fail olan testlere bug bağlayın
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Cycle Key</Label>
                      <Input
                        placeholder="PROJ-C123"
                        value={bugBaglaForm.cycleKey}
                        onChange={(e) => setBugBaglaForm(prev => ({ ...prev, cycleKey: e.target.value }))}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Bug Key</Label>
                      <Input
                        placeholder="PROJ-1234"
                        value={bugBaglaForm.bugKey}
                        onChange={(e) => setBugBaglaForm(prev => ({ ...prev, bugKey: e.target.value }))}
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
                          <span className="mr-1">{status.icon}</span>
                          {status.name}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <Button
                    onClick={handleBugBaglaAnalyze}
                    disabled={bugBaglaLoading}
                    className="w-full bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-500/90 hover:to-orange-500/90"
                  >
                    {bugBaglaLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Analiz Ediliyor...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 mr-2" />
                        Analiz Et
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Output Console */}
              <Card className="bg-card/50 backdrop-blur border-orange-500/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ChevronRight className="w-5 h-5 text-orange-500" />
                    Çıktı
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea 
                    className="h-[300px] rounded-lg bg-black/50 p-4 font-mono text-sm text-orange-400"
                  >
                    <pre className="whitespace-pre-wrap">
                      {bugBaglaOutput || "Çıktı burada görünecek..."}
                    </pre>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>

            {/* Results */}
            {bugBaglaResults && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
                    <CardContent className="p-6">
                      <p className="text-sm text-muted-foreground">Toplam Test</p>
                      <p className="text-3xl font-bold text-blue-400">{bugBaglaResults.stats.total}</p>
                    </CardContent>
                  </Card>
                  <Card className="bg-gradient-to-br from-red-500/10 to-red-600/5 border-red-500/20">
                    <CardContent className="p-6">
                      <p className="text-sm text-muted-foreground">Bağlanacak</p>
                      <p className="text-3xl font-bold text-red-400">{bugBaglaResults.stats.toBind}</p>
                    </CardContent>
                  </Card>
                </div>

                {bugBaglaResults.candidates.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>Bağlanacak Testler</span>
                        <Button
                          onClick={handleBindBugs}
                          disabled={bindingBugs}
                          className="bg-gradient-to-r from-green-500 to-emerald-500"
                        >
                          {bindingBugs ? (
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          ) : (
                            <Link2 className="w-4 h-4 mr-2" />
                          )}
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
                            <TableHead>Status</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {bugBaglaResults.candidates.map((item, idx) => (
                            <TableRow key={idx}>
                              <TableCell className="font-medium">{item.testKey}</TableCell>
                              <TableCell className="max-w-[300px] truncate">{item.testName}</TableCell>
                              <TableCell>
                                <Badge className={STATUS_INFO[item.status]?.color}>
                                  {STATUS_INFO[item.status]?.icon} {STATUS_INFO[item.status]?.name}
                                </Badge>
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

          {/* CYCLE ADD TAB - Placeholder */}
          <TabsContent value="cycleadd" className="space-y-6">
            <Card className="bg-card/50 backdrop-blur border-green-500/20">
              <CardContent className="p-12 text-center">
                <GitBranch className="w-16 h-16 mx-auto text-green-500/50 mb-4" />
                <h3 className="text-xl font-semibold mb-2">Cycle Add</h3>
                <p className="text-muted-foreground">
                  Cycle'a test ekleme özelliği yakında eklenecek
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          {/* API RERUN TAB - Placeholder */}
          <TabsContent value="rerun" className="space-y-6">
            <Card className="bg-card/50 backdrop-blur border-blue-500/20">
              <CardContent className="p-12 text-center">
                <RefreshCw className="w-16 h-16 mx-auto text-blue-500/50 mb-4" />
                <h3 className="text-xl font-semibold mb-2">API Rerun</h3>
                <p className="text-muted-foreground">
                  API test tekrar çalıştırma özelliği yakında eklenecek
                </p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </motion.div>
  );
};

export default JiraTools;
