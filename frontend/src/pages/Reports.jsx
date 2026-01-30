import { useEffect, useState, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Progress } from "../components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { 
  BarChart3,
  TrendingUp,
  CheckCircle2,
  Clock,
  ListTodo,
  PieChart,
  Download,
  FileText,
  FileSpreadsheet,
  Loader2,
  Calendar,
  Target,
  Wrench,
  TestTube,
  Bug,
  Award,
  Activity,
  ArrowUpRight,
  ArrowDownRight
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
  Cell,
  LineChart,
  Line,
  AreaChart,
  Area
} from "recharts";

const COLORS = ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'];
const WORK_COLORS = {
  maintenance: '#f59e0b',
  new_tests: '#10b981',
  bug_fixes: '#ef4444',
  other: '#6b7280'
};

const Reports = () => {
  const { user } = useAuth();
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [periodMonths, setPeriodMonths] = useState("1");
  const reportRef = useRef(null);

  useEffect(() => {
    if (user?.id) {
      fetchReportData();
    }
  }, [periodMonths, user?.id]);

  const fetchReportData = async () => {
    if (!user?.id) return;
    setLoading(true);
    try {
      const response = await api.get(`/reports/detailed-stats?period_months=${periodMonths}&user_id=${user.id}`);
      setReportData(response.data);
    } catch (error) {
      console.error("Error fetching report data:", error);
      toast.error("Rapor verileri alınamadı");
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
          user_id: user?.id,
          include_tasks: true,
          include_stats: true,
          period_months: parseInt(periodMonths)
        },
        { responseType: 'blob' }
      );
      
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      const extensions = { pdf: 'pdf', excel: 'xlsx', word: 'docx' };
      const periodLabel = periodMonths === "1" ? "1-ay" : periodMonths === "3" ? "3-ay" : periodMonths === "6" ? "6-ay" : "12-ay";
      a.download = `QA-Hub-Rapor-${periodLabel}-${new Date().toISOString().split('T')[0]}.${extensions[format]}`;
      
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success(`Rapor ${format.toUpperCase()} olarak indirildi`);
    } catch (error) {
      console.error("Export error:", error);
      toast.error("Rapor dışa aktarılırken hata oluştu");
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-violet-500" />
          <p className="text-muted-foreground">Rapor hazırlanıyor...</p>
        </div>
      </div>
    );
  }

  const { summary, work_breakdown, priority_breakdown, monthly_data, date_range, recent_tasks } = reportData || {};

  // Prepare chart data
  const workBreakdownData = [
    { name: 'Bakım', value: work_breakdown?.maintenance_tasks || 0, color: WORK_COLORS.maintenance },
    { name: 'Yeni Test', value: work_breakdown?.new_tests || 0, color: WORK_COLORS.new_tests },
    { name: 'Bug Fix', value: work_breakdown?.bug_fixes || 0, color: WORK_COLORS.bug_fixes },
    { name: 'Diğer', value: work_breakdown?.other || 0, color: WORK_COLORS.other }
  ].filter(item => item.value > 0);

  const priorityData = [
    { name: 'Kritik', value: priority_breakdown?.critical || 0, color: '#ef4444' },
    { name: 'Yüksek', value: priority_breakdown?.high || 0, color: '#f59e0b' },
    { name: 'Orta', value: priority_breakdown?.medium || 0, color: '#3b82f6' },
    { name: 'Düşük', value: priority_breakdown?.low || 0, color: '#10b981' }
  ].filter(item => item.value > 0);

  return (
    <div className="space-y-6" data-testid="reports-page" ref={reportRef}>
      {/* Header with Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg">
            <BarChart3 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent">
              Performans Raporu
            </h1>
            <p className="text-muted-foreground text-sm">
              {date_range?.start} - {date_range?.end}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Period Filter */}
          <Select value={periodMonths} onValueChange={setPeriodMonths}>
            <SelectTrigger className="w-[160px] border-violet-500/30" data-testid="period-select">
              <Calendar className="w-4 h-4 mr-2 text-violet-500" />
              <SelectValue placeholder="Dönem Seç" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">Son 1 Ay</SelectItem>
              <SelectItem value="3">Son 3 Ay</SelectItem>
              <SelectItem value="6">Son 6 Ay</SelectItem>
              <SelectItem value="12">Son 12 Ay</SelectItem>
            </SelectContent>
          </Select>

          {/* Export Buttons */}
          <Button 
            onClick={() => handleExport('pdf')}
            disabled={exporting}
            className="bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700"
            data-testid="export-pdf-btn"
          >
            {exporting ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <FileText className="w-4 h-4 mr-2" />
            )}
            PDF
          </Button>
          <Button 
            onClick={() => handleExport('excel')}
            disabled={exporting}
            variant="outline"
            className="border-emerald-500/50 text-emerald-600 hover:bg-emerald-50"
            data-testid="export-excel-btn"
          >
            <FileSpreadsheet className="w-4 h-4 mr-2" />
            Excel
          </Button>
        </div>
      </div>

      {/* User Info Banner */}
      <Card className="bg-gradient-to-r from-violet-500/10 via-purple-500/10 to-fuchsia-500/10 border-violet-500/20">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold">
                {reportData?.user_name?.charAt(0)?.toUpperCase() || 'U'}
              </div>
              <div>
                <h2 className="text-xl font-bold">{reportData?.user_name || 'Kullanıcı'}</h2>
                <p className="text-muted-foreground">QA Mühendisi</p>
                <Badge className="mt-1 bg-violet-500/20 text-violet-700 border-violet-500/30">
                  {reportData?.period_label}
                </Badge>
              </div>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <div className="text-center">
                <div className="text-3xl font-bold text-violet-600">{summary?.completion_rate || 0}%</div>
                <div className="text-sm text-muted-foreground">Tamamlanma</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-emerald-600">{summary?.completed_tasks || 0}</div>
                <div className="text-sm text-muted-foreground">Tamamlanan</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-amber-600">{summary?.total_tasks || 0}</div>
                <div className="text-sm text-muted-foreground">Toplam İş</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="relative overflow-hidden">
          <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-emerald-500/20 to-transparent rounded-bl-full" />
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
              </div>
              <div>
                <div className="text-2xl font-bold">{summary?.completed_tasks || 0}</div>
                <div className="text-xs text-muted-foreground">Tamamlanan</div>
              </div>
            </div>
            <div className="mt-2 flex items-center text-xs text-emerald-600">
              <ArrowUpRight className="w-3 h-3 mr-1" />
              <span>{summary?.completion_rate || 0}% oran</span>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden">
          <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-blue-500/20 to-transparent rounded-bl-full" />
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Activity className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <div className="text-2xl font-bold">{summary?.in_progress_tasks || 0}</div>
                <div className="text-xs text-muted-foreground">Devam Eden</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden">
          <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-amber-500/20 to-transparent rounded-bl-full" />
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <Wrench className="w-5 h-5 text-amber-500" />
              </div>
              <div>
                <div className="text-2xl font-bold">{work_breakdown?.maintenance_tasks || 0}</div>
                <div className="text-xs text-muted-foreground">Bakım</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden">
          <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-green-500/20 to-transparent rounded-bl-full" />
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                <TestTube className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <div className="text-2xl font-bold">{work_breakdown?.new_tests || 0}</div>
                <div className="text-xs text-muted-foreground">Yeni Test</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Work Distribution Pie Chart */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-lg">
              <PieChart className="w-5 h-5 text-violet-500" />
              İş Dağılımı
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsPie>
                  <Pie
                    data={workBreakdownData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {workBreakdownData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(255,255,255,0.95)', 
                      border: 'none', 
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)'
                    }}
                  />
                </RechartsPie>
              </ResponsiveContainer>
            </div>
            <div className="flex flex-wrap justify-center gap-4 mt-2">
              {workBreakdownData.map((item, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-sm text-muted-foreground">{item.name}: {item.value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Priority Distribution */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Target className="w-5 h-5 text-violet-500" />
              Öncelik Dağılımı
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {priorityData.map((item, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: item.color }} 
                      />
                      <span className="text-sm font-medium">{item.name}</span>
                    </div>
                    <span className="text-sm font-bold" style={{ color: item.color }}>
                      {item.value}
                    </span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div 
                      className="h-full rounded-full transition-all duration-500"
                      style={{ 
                        backgroundColor: item.color,
                        width: `${Math.max((item.value / Math.max(...priorityData.map(p => p.value), 1)) * 100, 5)}%`
                      }}
                    />
                  </div>
                </div>
              ))}
              {priorityData.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  Öncelik verisi bulunamadı
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Trend */}
      {monthly_data && monthly_data.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-lg">
              <TrendingUp className="w-5 h-5 text-violet-500" />
              Aylık Performans Trendi
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={monthly_data}>
                  <defs>
                    <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorCompleted" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                  <YAxis />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(255,255,255,0.95)', 
                      border: 'none', 
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)'
                    }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="total" 
                    stroke="#8b5cf6" 
                    fillOpacity={1} 
                    fill="url(#colorTotal)" 
                    strokeWidth={2}
                    name="Toplam"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="completed" 
                    stroke="#10b981" 
                    fillOpacity={1} 
                    fill="url(#colorCompleted)" 
                    strokeWidth={2}
                    name="Tamamlanan"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Completion Rate Progress */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Award className="w-5 h-5 text-violet-500" />
            Performans Özeti
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Genel Tamamlanma Oranı</span>
                <span className="text-sm font-bold text-violet-600">{summary?.completion_rate || 0}%</span>
              </div>
              <Progress value={summary?.completion_rate || 0} className="h-3 bg-violet-100" />
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
              <div className="text-center p-3 rounded-lg bg-gradient-to-br from-violet-50 to-purple-50">
                <div className="text-2xl font-bold text-violet-600">{summary?.total_tasks || 0}</div>
                <div className="text-xs text-muted-foreground">Toplam Görev</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-gradient-to-br from-emerald-50 to-green-50">
                <div className="text-2xl font-bold text-emerald-600">{summary?.completed_tasks || 0}</div>
                <div className="text-xs text-muted-foreground">Tamamlanan</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-gradient-to-br from-amber-50 to-orange-50">
                <div className="text-2xl font-bold text-amber-600">{work_breakdown?.maintenance_tasks || 0}</div>
                <div className="text-xs text-muted-foreground">Bakım İşlemi</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-gradient-to-br from-cyan-50 to-blue-50">
                <div className="text-2xl font-bold text-cyan-600">{work_breakdown?.new_tests || 0}</div>
                <div className="text-xs text-muted-foreground">Yeni Test</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      {recent_tasks && recent_tasks.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Clock className="w-5 h-5 text-violet-500" />
              Son Aktiviteler
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recent_tasks.slice(0, 5).map((task, i) => (
                <div 
                  key={i} 
                  className="flex items-center justify-between p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "w-2 h-2 rounded-full",
                      task.status === "completed" ? "bg-emerald-500" :
                      task.status === "in_progress" ? "bg-blue-500" : "bg-gray-400"
                    )} />
                    <span className="font-medium text-sm">{task.title || "Görev"}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className={cn(
                      "text-xs",
                      task.priority === "critical" ? "border-red-500 text-red-600" :
                      task.priority === "high" ? "border-amber-500 text-amber-600" :
                      task.priority === "medium" ? "border-blue-500 text-blue-600" :
                      "border-gray-500 text-gray-600"
                    )}>
                      {task.priority || "normal"}
                    </Badge>
                    <span className="text-xs text-muted-foreground">{task.created_at}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Footer */}
      <div className="text-center text-sm text-muted-foreground py-4 border-t">
        <p>QA Hub - Performans Raporu • Oluşturulma: {new Date().toLocaleDateString('tr-TR')}</p>
      </div>
    </div>
  );
};

export default Reports;
