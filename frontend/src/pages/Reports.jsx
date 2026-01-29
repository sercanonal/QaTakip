import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Progress } from "../components/ui/progress";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { 
  BarChart3,
  TrendingUp,
  CheckCircle2,
  Clock,
  ListTodo,
  AlertTriangle,
  PieChart,
  Download,
  FileText,
  FileSpreadsheet,
  FileImage,
  Loader2
} from "lucide-react";
import { cn } from "../lib/utils";
import { toast } from "sonner";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPie,
  Pie,
  Cell
} from "recharts";

const priorityLabels = {
  low: "Düşük",
  medium: "Orta",
  high: "Yüksek",
  critical: "Kritik"
};

const Reports = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, tasksRes] = await Promise.all([
        api.get("/dashboard/stats"),
        api.get("/tasks")
      ]);
      setStats(statsRes.data);
      setTasks(tasksRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    setExporting(true);
    try {
      const response = await api.post('/reports/export', 
        {
          format,
          user_id: user.id,
          include_tasks: true,
          include_stats: true
        },
        {
          responseType: 'blob'
        }
      );
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const extensions = { pdf: 'pdf', excel: 'xlsx', word: 'docx' };
      link.setAttribute('download', `qa_report_${Date.now()}.${extensions[format]}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success(`Rapor ${format.toUpperCase()} formatında indirildi`);
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Rapor dışa aktarılırken hata oluştu');
    } finally {
      setExporting(false);
    }
  };

  const getCategoryName = (categoryId) => {
    const category = user?.categories?.find(c => c.id === categoryId);
    return category?.name || categoryId;
  };

  const getCategoryColor = (categoryId) => {
    const category = user?.categories?.find(c => c.id === categoryId);
    return category?.color || "#3B82F6";
  };

  // Prepare chart data
  const categoryChartData = user?.categories?.map(cat => ({
    name: cat.name,
    count: stats?.category_stats?.[cat.id] || 0,
    color: cat.color
  })).filter(c => c.count > 0) || [];

  const statusChartData = [
    { name: "Yapılacak", value: stats?.todo_tasks || 0, color: "#71717A" },
    { name: "Devam Ediyor", value: stats?.in_progress_tasks || 0, color: "#3B82F6" },
    { name: "Tamamlandı", value: stats?.completed_tasks || 0, color: "#10B981" }
  ].filter(s => s.value > 0);

  const priorityChartData = [
    { name: "Düşük", value: stats?.priority_stats?.low || 0, color: "#71717A" },
    { name: "Orta", value: stats?.priority_stats?.medium || 0, color: "#F59E0B" },
    { name: "Yüksek", value: stats?.priority_stats?.high || 0, color: "#E11D48" },
    { name: "Kritik", value: stats?.priority_stats?.critical || 0, color: "#EF4444" }
  ].filter(p => p.value > 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div>
        <h2 className="font-heading text-2xl font-bold">Raporlar</h2>
        <p className="text-muted-foreground">Performans ve ilerleme analizleri</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-border/50 bg-card card-hover">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Toplam Görev</p>
                <p className="text-3xl font-heading font-bold">{stats?.total_tasks || 0}</p>
              </div>
              <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                <ListTodo className="w-6 h-6 text-primary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50 bg-card card-hover">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Tamamlanan</p>
                <p className="text-3xl font-heading font-bold text-success">{stats?.completed_tasks || 0}</p>
              </div>
              <div className="w-12 h-12 rounded-full bg-success/20 flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6 text-success" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50 bg-card card-hover">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Devam Eden</p>
                <p className="text-3xl font-heading font-bold text-info">{stats?.in_progress_tasks || 0}</p>
              </div>
              <div className="w-12 h-12 rounded-full bg-info/20 flex items-center justify-center">
                <Clock className="w-6 h-6 text-info" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50 bg-card card-hover">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Geciken</p>
                <p className="text-3xl font-heading font-bold text-destructive">{stats?.overdue_tasks || 0}</p>
              </div>
              <div className="w-12 h-12 rounded-full bg-destructive/20 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-destructive" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Completion Progress */}
      <Card className="border-border/50 bg-card">
        <CardHeader>
          <CardTitle className="font-heading flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary" />
            Tamamlanma Oranı
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-end gap-4 mb-4">
            <span className="text-5xl font-heading font-bold text-primary">
              {stats?.completion_rate || 0}%
            </span>
            <span className="text-muted-foreground pb-1">tamamlandı</span>
          </div>
          <Progress value={stats?.completion_rate || 0} className="h-4" />
          <p className="text-sm text-muted-foreground mt-2">
            {stats?.completed_tasks || 0} / {stats?.total_tasks || 0} görev tamamlandı
          </p>
        </CardContent>
      </Card>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Distribution */}
        <Card className="border-border/50 bg-card">
          <CardHeader>
            <CardTitle className="font-heading flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-primary" />
              Kategorilere Göre Dağılım
            </CardTitle>
          </CardHeader>
          <CardContent>
            {categoryChartData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={categoryChartData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                    <XAxis type="number" stroke="#71717A" />
                    <YAxis dataKey="name" type="category" stroke="#71717A" width={100} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#18181B",
                        border: "1px solid #27272A",
                        borderRadius: "8px"
                      }}
                    />
                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                      {categoryChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Veri yok
              </div>
            )}
          </CardContent>
        </Card>

        {/* Status Distribution */}
        <Card className="border-border/50 bg-card">
          <CardHeader>
            <CardTitle className="font-heading flex items-center gap-2">
              <PieChart className="w-5 h-5 text-primary" />
              Durum Dağılımı
            </CardTitle>
          </CardHeader>
          <CardContent>
            {statusChartData.length > 0 ? (
              <div className="h-64 flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPie>
                    <Pie
                      data={statusChartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {statusChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#18181B",
                        border: "1px solid #27272A",
                        borderRadius: "8px"
                      }}
                    />
                  </RechartsPie>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Veri yok
              </div>
            )}
            {statusChartData.length > 0 && (
              <div className="flex justify-center gap-4 mt-4">
                {statusChartData.map((item) => (
                  <div key={item.name} className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-sm text-muted-foreground">
                      {item.name}: {item.value}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Priority Breakdown */}
      <Card className="border-border/50 bg-card">
        <CardHeader>
          <CardTitle className="font-heading">Öncelik Dağılımı</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(priorityLabels).map(([key, label]) => {
              const count = stats?.priority_stats?.[key] || 0;
              const percentage = stats?.total_tasks > 0 
                ? Math.round((count / stats.total_tasks) * 100) 
                : 0;
              return (
                <div key={key} className="p-4 rounded-lg bg-secondary/30 border border-border/50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">{label}</span>
                    <Badge variant="secondary" className="font-mono">{count}</Badge>
                  </div>
                  <Progress value={percentage} className="h-2" />
                  <p className="text-xs text-muted-foreground mt-1">{percentage}%</p>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Reports;
