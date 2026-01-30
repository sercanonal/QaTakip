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
import { toast } from "sonner";
import { 
  Search,
  Loader2,
  Users,
  AlertCircle,
  Clock,
  ListTodo,
  Lock,
  ExternalLink,
  Key,
  ShieldCheck,
  Settings,
} from "lucide-react";

const STATUS_COLORS = {
  'in_progress': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  'backlog': 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30',
};

const PRIORITY_LABELS = {
  'critical': 'Kritik',
  'high': 'Yüksek',
  'medium': 'Orta',
  'low': 'Düşük',
};

const PRIORITY_COLORS = {
  'critical': 'bg-red-500/20 text-red-400 border-red-500/30',
  'high': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  'medium': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  'low': 'bg-green-500/20 text-green-400 border-green-500/30',
};

const TeamTracking = () => {
  const [loading, setLoading] = useState(true);
  const [keyExists, setKeyExists] = useState(false);
  const [adminKey, setAdminKey] = useState("");
  const [newKey, setNewKey] = useState("");
  const [confirmKey, setConfirmKey] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [searchUsername, setSearchUsername] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState(null);

  useEffect(() => {
    checkKeyStatus();
  }, []);

  const checkKeyStatus = async () => {
    try {
      const response = await api.get('/admin/key-exists');
      setKeyExists(response.data.exists);
      
      // Check if we have a saved key in session
      const savedKey = sessionStorage.getItem('admin_key');
      if (savedKey && response.data.exists) {
        verifyKey(savedKey);
      }
    } catch (error) {
      console.error("Error checking key status:", error);
    } finally {
      setLoading(false);
    }
  };

  const setupKey = async (e) => {
    e.preventDefault();
    
    if (!newKey || newKey.length < 6) {
      toast.error("Anahtar en az 6 karakter olmalı");
      return;
    }
    
    if (newKey !== confirmKey) {
      toast.error("Anahtarlar eşleşmiyor");
      return;
    }
    
    setVerifying(true);
    try {
      const response = await api.post('/admin/setup-key', { admin_key: newKey });
      if (response.data.success) {
        toast.success("Admin anahtarı başarıyla oluşturuldu!");
        setKeyExists(true);
        setAdminKey(newKey);
        sessionStorage.setItem('admin_key', newKey);
        setIsAuthenticated(true);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Anahtar oluşturulamadı");
    } finally {
      setVerifying(false);
    }
  };

  const verifyKey = async (key) => {
    setVerifying(true);
    try {
      const response = await api.post('/admin/verify-key', { admin_key: key });
      if (response.data.valid) {
        setIsAuthenticated(true);
        setAdminKey(key);
        sessionStorage.setItem('admin_key', key);
        toast.success("Giriş başarılı!");
      } else {
        setIsAuthenticated(false);
        sessionStorage.removeItem('admin_key');
        toast.error("Geçersiz anahtar");
      }
    } catch (error) {
      setIsAuthenticated(false);
      toast.error("Doğrulama başarısız");
    } finally {
      setVerifying(false);
    }
  };

  const handleKeySubmit = (e) => {
    e.preventDefault();
    if (!adminKey.trim()) {
      toast.error("Anahtar girin");
      return;
    }
    verifyKey(adminKey);
  };

  const handleSearch = async () => {
    if (!searchUsername.trim()) {
      toast.error("Kullanıcı adı girin");
      return;
    }

    setSearching(true);
    setSearchResult(null);

    try {
      const response = await api.get(
        `/admin/team-tasks?search_username=${encodeURIComponent(searchUsername)}&admin_key=${encodeURIComponent(adminKey)}`
      );
      setSearchResult(response.data);
      
      if (response.data.found) {
        toast.success(`${response.data.summary?.total || 0} görev bulundu`);
      }
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("Erişim reddedildi");
        setIsAuthenticated(false);
        sessionStorage.removeItem('admin_key');
      } else {
        toast.error("Arama yapılamadı");
      }
    } finally {
      setSearching(false);
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setAdminKey("");
    setSearchResult(null);
    sessionStorage.removeItem('admin_key');
    toast.info("Çıkış yapıldı");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
      </div>
    );
  }

  // First time setup - no key exists
  if (!keyExists) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="w-full max-w-md border-border/50 bg-card">
          <CardHeader className="text-center">
            <div className="w-16 h-16 rounded-full bg-violet-500/10 flex items-center justify-center mx-auto mb-4">
              <Settings className="w-8 h-8 text-violet-500" />
            </div>
            <CardTitle className="text-xl">İlk Kurulum</CardTitle>
            <CardDescription>
              Ekip Takibi özelliği için bir admin anahtarı belirleyin.
              <br />
              <span className="text-amber-500 text-xs font-medium">Bu anahtar sadece veritabanında saklanır, kod içinde görünmez.</span>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={setupKey} className="space-y-4">
              <div>
                <label className="text-sm text-muted-foreground mb-1 block">Yeni Anahtar</label>
                <div className="relative">
                  <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    type="password"
                    placeholder="En az 6 karakter..."
                    value={newKey}
                    onChange={(e) => setNewKey(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm text-muted-foreground mb-1 block">Anahtar Tekrar</label>
                <div className="relative">
                  <ShieldCheck className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    type="password"
                    placeholder="Anahtarı tekrar girin..."
                    value={confirmKey}
                    onChange={(e) => setConfirmKey(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <Button 
                type="submit" 
                className="w-full bg-violet-600 hover:bg-violet-700"
                disabled={verifying}
              >
                {verifying ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <ShieldCheck className="w-4 h-4 mr-2" />
                )}
                Anahtarı Kaydet
              </Button>
            </form>
            <p className="text-xs text-muted-foreground text-center mt-4">
              Bu anahtarı not alın ve sadece yetki vermek istediğiniz kişilerle paylaşın.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Key exists but not authenticated - show login
  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="w-full max-w-md border-border/50 bg-card">
          <CardHeader className="text-center">
            <div className="w-16 h-16 rounded-full bg-violet-500/10 flex items-center justify-center mx-auto mb-4">
              <Lock className="w-8 h-8 text-violet-500" />
            </div>
            <CardTitle className="text-xl">Ekip Takibi</CardTitle>
            <CardDescription>
              Bu özelliğe erişmek için admin anahtarı gereklidir.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleKeySubmit} className="space-y-4">
              <div className="relative">
                <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  type="password"
                  placeholder="Admin anahtarını girin..."
                  value={adminKey}
                  onChange={(e) => setAdminKey(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button 
                type="submit" 
                className="w-full"
                disabled={verifying}
              >
                {verifying ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <Lock className="w-4 h-4 mr-2" />
                )}
                Giriş Yap
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Authenticated - show team tracking
  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-heading text-2xl font-bold flex items-center gap-2">
            <Users className="w-6 h-6 text-violet-500" />
            Ekip Takibi
          </h2>
          <p className="text-muted-foreground">
            Jira'dan ekip üyelerinin görevlerini görüntüleyin
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleLogout}>
          Çıkış
        </Button>
      </div>

      <Card className="border-border/50 bg-card">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Search className="w-5 h-5 text-violet-500" />
            Jira Kullanıcı Ara
          </CardTitle>
          <CardDescription>
            Jira/AD kullanıcı adı ile arama yapın
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="Kullanıcı adı (örn: sercano)"
              value={searchUsername}
              onChange={(e) => setSearchUsername(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1"
            />
            <Button onClick={handleSearch} disabled={searching}>
              {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4 mr-2" />}
              {!searching && "Ara"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {searchResult && (
        <Card className="border-border/50 bg-card">
          <CardHeader>
            {searchResult.found ? (
              <>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Users className="w-5 h-5 text-violet-500" />
                  {searchResult.user?.name}
                  <Badge variant="outline" className="ml-2 bg-violet-500/10 text-violet-400">Jira</Badge>
                </CardTitle>
                <CardDescription>
                  <div className="flex gap-4 mt-2">
                    <Badge variant="outline" className="bg-blue-500/10 text-blue-400">
                      <Clock className="w-3 h-3 mr-1" />
                      Devam Eden: {searchResult.summary?.in_progress || 0}
                    </Badge>
                    <Badge variant="outline" className="bg-zinc-500/10 text-zinc-400">
                      <ListTodo className="w-3 h-3 mr-1" />
                      Backlog: {searchResult.summary?.backlog || 0}
                    </Badge>
                  </div>
                </CardDescription>
              </>
            ) : (
              <CardTitle className="text-lg flex items-center gap-2 text-amber-500">
                <AlertCircle className="w-5 h-5" />
                {searchResult.message}
              </CardTitle>
            )}
          </CardHeader>
          
          {searchResult.found && searchResult.tasks?.length > 0 && (
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Görev</TableHead>
                    <TableHead>Durum</TableHead>
                    <TableHead>Öncelik</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {searchResult.tasks.map((task) => (
                    <TableRow key={task.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{task.title}</span>
                          {task.jira_key && (
                            <a 
                              href={`https://jira.intertech.com.tr/browse/${task.jira_key}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-violet-500 hover:text-violet-400"
                            >
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={STATUS_COLORS[task.status] || ''}>
                          {task.jira_status || task.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={PRIORITY_COLORS[task.priority] || ''}>
                          {PRIORITY_LABELS[task.priority] || task.priority}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          )}
          
          {searchResult.found && searchResult.tasks?.length === 0 && (
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <ListTodo className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Bu kullanıcının açık görevi yok</p>
              </div>
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
};

export default TeamTracking;
