import { useState, useEffect } from "react";
import api from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
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
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { toast } from "sonner";
import { 
  Loader2,
  Users,
  Clock,
  ListTodo,
  Lock,
  ExternalLink,
  Key,
  CheckCircle2,
  RefreshCw,
  TrendingUp,
  Calendar,
  ChevronRight,
  BarChart3,
  LogOut,
} from "lucide-react";

const PRIORITY_COLORS = {
  'Blocker': 'bg-red-500/20 text-red-400 border-red-500/30',
  'Critical': 'bg-red-500/20 text-red-400 border-red-500/30',
  'Highest': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  'High': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  'Major': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  'Medium': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  'Low': 'bg-green-500/20 text-green-400 border-green-500/30',
  'Minor': 'bg-green-500/20 text-green-400 border-green-500/30',
  'Lowest': 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30',
};

const TeamTracking = () => {
  const [inputVal, setInputVal] = useState("");
  const [isAuth, setIsAuth] = useState(false);
  const [checking, setChecking] = useState(false);
  const [storedVal, setStoredVal] = useState("");
  
  // Dashboard state
  const [loading, setLoading] = useState(false);
  const [teamData, setTeamData] = useState([]);
  const [totals, setTotals] = useState(null);
  const [periodMonths, setPeriodMonths] = useState(1);
  const [dateRange, setDateRange] = useState(null);
  
  // Detail modal state
  const [selectedUser, setSelectedUser] = useState(null);
  const [userTasks, setUserTasks] = useState(null);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputVal.trim()) return;
    
    setChecking(true);
    try {
      const res = await api.post('/admin/verify-key', { v: inputVal });
      if (res.data.r) {
        setIsAuth(true);
        setStoredVal(inputVal);
        toast.success("Doğrulandı");
      } else {
        toast.error("Geçersiz");
      }
    } catch {
      toast.error("Hata");
    } finally {
      setChecking(false);
    }
  };

  const loadTeamSummary = async (months = periodMonths) => {
    setLoading(true);
    try {
      const res = await api.get(`/admin/team-summary?t=${encodeURIComponent(storedVal)}&months=${months}`);
      
      if (res.data.success) {
        setTeamData(res.data.team || []);
        setTotals(res.data.totals);
        setDateRange(res.data.date_range);
        if (res.data.team?.length > 0) {
          toast.success(`${res.data.team.length} ekip üyesi yüklendi`);
        } else {
          toast.info("Ekip üyesi bulunamadı");
        }
      } else {
        toast.error(res.data.error || "Veriler yüklenemedi");
      }
    } catch (error) {
      toast.error("Ekip verileri alınamadı");
    } finally {
      setLoading(false);
    }
  };

  const loadUserTasks = async (username, displayName) => {
    setSelectedUser({ username, displayName });
    setDetailOpen(true);
    setLoadingTasks(true);
    setUserTasks(null);
    
    try {
      const res = await api.get(
        `/admin/user-tasks-detail?username=${encodeURIComponent(username)}&t=${encodeURIComponent(storedVal)}&months=${periodMonths}`
      );
      
      if (res.data.success) {
        setUserTasks(res.data);
      } else {
        toast.error(res.data.error || "Görevler yüklenemedi");
      }
    } catch (error) {
      toast.error("Görevler alınamadı");
    } finally {
      setLoadingTasks(false);
    }
  };

  const handlePeriodChange = (value) => {
    const months = parseInt(value);
    setPeriodMonths(months);
    loadTeamSummary(months);
  };

  const handleExit = () => {
    setIsAuth(false);
    setStoredVal("");
    setInputVal("");
    setTeamData([]);
    setTotals(null);
  };

  // Load data on auth
  useEffect(() => {
    if (isAuth && storedVal) {
      loadTeamSummary();
    }
  }, [isAuth]);

  // Auth screen
  if (!isAuth) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="w-full max-w-md border-border/50 bg-card" data-testid="auth-card">
          <CardHeader className="text-center">
            <div className="w-16 h-16 rounded-full bg-violet-500/10 flex items-center justify-center mx-auto mb-4">
              <Lock className="w-8 h-8 text-violet-500" />
            </div>
            <CardTitle className="text-xl">Erişim Doğrulama</CardTitle>
            <CardDescription>Devam etmek için doğrulama gerekli</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="relative">
                <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  type="password"
                  placeholder="..."
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                  className="pl-10"
                  data-testid="auth-input"
                />
              </div>
              <Button type="submit" className="w-full" disabled={checking} data-testid="auth-submit">
                {checking ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Lock className="w-4 h-4 mr-2" />}
                Doğrula
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="team-tracking-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="font-heading text-2xl font-bold flex items-center gap-2">
            <Users className="w-6 h-6 text-violet-500" />
            Ekip Takibi Panosu
          </h2>
          <p className="text-muted-foreground text-sm">Kalite Güvence ekibinin Jira görevlerini izleyin</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={String(periodMonths)} onValueChange={handlePeriodChange}>
            <SelectTrigger className="w-[140px]" data-testid="period-select">
              <Calendar className="w-4 h-4 mr-2 text-violet-500" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">Son 1 Ay</SelectItem>
              <SelectItem value="3">Son 3 Ay</SelectItem>
              <SelectItem value="6">Son 6 Ay</SelectItem>
              <SelectItem value="12">Son 12 Ay</SelectItem>
            </SelectContent>
          </Select>
          <Button 
            variant="outline" 
            size="icon" 
            onClick={() => loadTeamSummary()}
            disabled={loading}
            data-testid="refresh-btn"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
          <Button variant="outline" size="sm" onClick={handleExit} data-testid="exit-btn">
            <LogOut className="w-4 h-4 mr-2" />
            Çıkış
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {totals && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border-border/50 bg-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Ekip Üyesi</p>
                  <p className="text-2xl font-bold">{totals.total_users}</p>
                </div>
                <Users className="w-8 h-8 text-violet-500 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-border/50 bg-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Backlog</p>
                  <p className="text-2xl font-bold text-zinc-400">{totals.total_backlog}</p>
                  <p className="text-xs text-muted-foreground mt-1">Tüm açık</p>
                </div>
                <ListTodo className="w-8 h-8 text-zinc-500 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-border/50 bg-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Devam Eden</p>
                  <p className="text-2xl font-bold text-blue-400">{totals.total_in_progress}</p>
                  <p className="text-xs text-muted-foreground mt-1">Tüm açık</p>
                </div>
                <Clock className="w-8 h-8 text-blue-500 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-border/50 bg-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Tamamlanan</p>
                  <p className="text-2xl font-bold text-green-400">{totals.total_completed}</p>
                  <p className="text-xs text-muted-foreground mt-1">Son {periodMonths} ay</p>
                </div>
                <CheckCircle2 className="w-8 h-8 text-green-500 opacity-50" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Date Range Info */}
      {dateRange && (
        <div className="text-xs text-muted-foreground flex items-center gap-2">
          <Calendar className="w-3 h-3" />
          <span>Tarih Aralığı: {dateRange.start} - {dateRange.end}</span>
        </div>
      )}

      {/* Team Table */}
      <Card className="border-border/50 bg-card">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-violet-500" />
            Ekip Performansı
          </CardTitle>
          <CardDescription>
            Kullanıcı ismine tıklayarak detaylı görev listesini görüntüleyin
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
              <span className="ml-3 text-muted-foreground">Veriler yükleniyor...</span>
            </div>
          ) : teamData.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Henüz ekip verisi yok</p>
              <Button 
                variant="outline" 
                className="mt-4"
                onClick={() => loadTeamSummary()}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Verileri Yükle
              </Button>
            </div>
          ) : (
            <div className="rounded-md border border-border/50 overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/30 hover:bg-muted/30">
                    <TableHead className="font-semibold">Kullanıcı</TableHead>
                    <TableHead className="text-center font-semibold">
                      <span className="flex items-center justify-center gap-1">
                        <ListTodo className="w-4 h-4 text-zinc-400" />
                        Backlog
                      </span>
                    </TableHead>
                    <TableHead className="text-center font-semibold">
                      <span className="flex items-center justify-center gap-1">
                        <Clock className="w-4 h-4 text-blue-400" />
                        Devam Eden
                      </span>
                    </TableHead>
                    <TableHead className="text-center font-semibold">
                      <span className="flex items-center justify-center gap-1">
                        <CheckCircle2 className="w-4 h-4 text-green-400" />
                        Tamamlanan
                      </span>
                    </TableHead>
                    <TableHead className="text-center font-semibold">
                      <span className="flex items-center justify-center gap-1">
                        <TrendingUp className="w-4 h-4 text-violet-400" />
                        Toplam Aktif
                      </span>
                    </TableHead>
                    <TableHead className="w-[50px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {teamData.map((user, idx) => (
                    <TableRow 
                      key={user.username || idx}
                      className="cursor-pointer hover:bg-violet-500/5 transition-colors"
                      onClick={() => loadUserTasks(user.username, user.displayName)}
                      data-testid={`team-row-${user.username}`}
                    >
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500/20 to-blue-500/20 flex items-center justify-center text-sm font-medium text-violet-400 border border-violet-500/20">
                            {(user.displayName || user.username || '?').charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium">{user.displayName || user.username}</p>
                            <p className="text-xs text-muted-foreground">{user.username}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="outline" className="bg-zinc-500/10 text-zinc-400 border-zinc-500/30 min-w-[40px]">
                          {user.backlog}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30 min-w-[40px]">
                          {user.in_progress}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/30 min-w-[40px]">
                          {user.completed}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="outline" className="bg-violet-500/10 text-violet-400 border-violet-500/30 min-w-[40px] font-semibold">
                          {user.total_active}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <ChevronRight className="w-4 h-4 text-muted-foreground" />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* User Detail Modal */}
      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500/20 to-blue-500/20 flex items-center justify-center text-lg font-medium text-violet-400 border border-violet-500/20">
                {(selectedUser?.displayName || '?').charAt(0).toUpperCase()}
              </div>
              <div>
                <p>{selectedUser?.displayName}</p>
                <p className="text-sm font-normal text-muted-foreground">{selectedUser?.username}</p>
              </div>
            </DialogTitle>
          </DialogHeader>
          
          {loadingTasks ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
            </div>
          ) : userTasks ? (
            <div className="flex-1 overflow-auto">
              {/* Task Counts Summary */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-zinc-500/10 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-zinc-400">{userTasks.counts?.backlog || 0}</p>
                  <p className="text-xs text-muted-foreground">Backlog</p>
                </div>
                <div className="bg-blue-500/10 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-blue-400">{userTasks.counts?.in_progress || 0}</p>
                  <p className="text-xs text-muted-foreground">Devam Eden</p>
                </div>
                <div className="bg-green-500/10 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-green-400">{userTasks.counts?.completed || 0}</p>
                  <p className="text-xs text-muted-foreground">Tamamlanan</p>
                </div>
              </div>

              {/* Tasks Tabs */}
              <Tabs defaultValue="in_progress" className="w-full">
                <TabsList className="w-full grid grid-cols-3">
                  <TabsTrigger value="backlog" className="flex items-center gap-1">
                    <ListTodo className="w-4 h-4" />
                    Backlog ({userTasks.counts?.backlog || 0})
                  </TabsTrigger>
                  <TabsTrigger value="in_progress" className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    Devam Eden ({userTasks.counts?.in_progress || 0})
                  </TabsTrigger>
                  <TabsTrigger value="completed" className="flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" />
                    Tamamlanan ({userTasks.counts?.completed || 0})
                  </TabsTrigger>
                </TabsList>

                {['backlog', 'in_progress', 'completed'].map(tabKey => (
                  <TabsContent key={tabKey} value={tabKey} className="mt-4">
                    {(userTasks.tasks?.[tabKey] || []).length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <p>Bu kategoride görev yok</p>
                      </div>
                    ) : (
                      <div className="space-y-2 max-h-[400px] overflow-auto pr-2">
                        {(userTasks.tasks?.[tabKey] || []).map((task, idx) => (
                          <div 
                            key={task.key || idx}
                            className="p-3 rounded-lg border border-border/50 bg-card/50 hover:bg-card transition-colors"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <a 
                                    href={task.jira_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-violet-400 hover:text-violet-300 font-mono text-sm"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    {task.key}
                                    <ExternalLink className="w-3 h-3 inline ml-1" />
                                  </a>
                                  <Badge variant="outline" className="text-xs">
                                    {task.issueType}
                                  </Badge>
                                </div>
                                <p className="text-sm font-medium truncate">{task.summary}</p>
                                <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                                  <span>{task.project}</span>
                                  <span>•</span>
                                  <span>{task.created}</span>
                                </div>
                              </div>
                              <div className="flex flex-col items-end gap-1">
                                <Badge 
                                  variant="outline" 
                                  className={PRIORITY_COLORS[task.priority] || 'bg-zinc-500/10'}
                                >
                                  {task.priority}
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                  {task.status}
                                </Badge>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </TabsContent>
                ))}
              </Tabs>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <p>Veriler yüklenemedi</p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TeamTracking;
