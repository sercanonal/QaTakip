import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
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
  Plus,
  Trash2,
  Loader2,
  User,
  Tag,
  Palette,
  FolderKanban,
  Edit3,
  GitBranch,
} from "lucide-react";
import { cn } from "../lib/utils";

const colorOptions = [
  "#E11D48", "#F43F5E", "#EF4444", "#F59E0B", "#FBBF24",
  "#10B981", "#14B8A6", "#06B6D4", "#3B82F6", "#6366F1",
  "#8B5CF6", "#A855F7", "#D946EF", "#EC4899", "#71717A"
];

const Settings = () => {
  const { user, updateUser, logout } = useAuth();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  
  // QA Projects State
  const [qaProjects, setQaProjects] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [isProjectDialogOpen, setIsProjectDialogOpen] = useState(false);
  const [isCycleDialogOpen, setIsCycleDialogOpen] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [editingCycle, setEditingCycle] = useState(null);
  const [projectSaving, setProjectSaving] = useState(false);
  const [cycleSaving, setCycleSaving] = useState(false);
  
  const [newProject, setNewProject] = useState({ name: "", icon: "📦" });
  const [newCycle, setNewCycle] = useState({ key: "", name: "" });
  
  const [newCategory, setNewCategory] = useState({
    name: "",
    color: "#3B82F6"
  });

  // Emoji list for project icons
  const emojiList = ["📦", "🖥️", "💻", "🚀", "⚙️", "🔧", "📱", "🌐", "💡", "📊", "🎯", "✅", "⚡", "🔥", "💰", "🎨", "📝", "📌", "🔐", "⭐"];

  // Load QA Projects and Cycles on mount
  useEffect(() => {
    loadQaProjects();
    loadCycles();
  }, []);

  const loadQaProjects = async () => {
    try {
      const response = await api.get("/qa-projects");
      setQaProjects(response.data.projects || []);
    } catch (error) {
      console.error("QA Projects yüklenemedi:", error);
    }
  };

  const loadCycles = async () => {
    try {
      const response = await api.get("/cycles");
      setCycles(response.data.cycles || []);
    } catch (error) {
      console.error("Cycles yüklenemedi:", error);
    }
  };

  const handleAddProject = async () => {
    if (!newProject.name.trim()) {
      toast.error("Proje adı gerekli!");
      return;
    }
    
    setProjectSaving(true);
    try {
      await api.post("/qa-projects", newProject);
      toast.success("Proje eklendi!");
      setNewProject({ name: "", icon: "📦" });
      setIsProjectDialogOpen(false);
      loadQaProjects();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Proje eklenemedi");
    } finally {
      setProjectSaving(false);
    }
  };

  const handleUpdateProject = async () => {
    if (!editingProject || !editingProject.name.trim()) {
      toast.error("Proje adı gerekli!");
      return;
    }
    
    setProjectSaving(true);
    try {
      await api.put(`/qa-projects/${encodeURIComponent(editingProject.originalName)}`, editingProject);
      toast.success("Proje güncellendi!");
      setEditingProject(null);
      loadQaProjects();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Proje güncellenemedi");
    } finally {
      setProjectSaving(false);
    }
  };

  const handleDeleteProject = async (name) => {
    if (!window.confirm(`"${name}" projesini silmek istediğinize emin misiniz?`)) return;
    
    try {
      await api.delete(`/qa-projects/${encodeURIComponent(name)}`);
      toast.success("Proje silindi!");
      loadQaProjects();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Proje silinemedi");
    }
  };

  const handleAddCycle = async () => {
    if (!newCycle.key.trim() || !newCycle.name.trim()) {
      toast.error("Cycle key ve adı gerekli!");
      return;
    }
    
    setCycleSaving(true);
    try {
      await api.post("/cycles", newCycle);
      toast.success("Cycle eklendi!");
      setNewCycle({ key: "", name: "" });
      setIsCycleDialogOpen(false);
      loadCycles();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Cycle eklenemedi");
    } finally {
      setCycleSaving(false);
    }
  };

  const handleDeleteCycle = async (key) => {
    if (!window.confirm(`"${key}" cycle'ını silmek istediğinize emin misiniz?`)) return;
    
    try {
      await api.delete(`/cycles/${encodeURIComponent(key)}`);
      toast.success("Cycle silindi!");
      loadCycles();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Cycle silinemedi");
    }
  };

  const handleAddCategory = async (e) => {
    e.preventDefault();
    
    if (!newCategory.name.trim()) {
      toast.error("Kategori adı gerekli");
      return;
    }
    
    setSaving(true);
    
    try {
      const response = await api.post(`/users/${user.id}/categories`, {
        id: newCategory.name.toLowerCase().replace(/\s+/g, "-"),
        name: newCategory.name,
        color: newCategory.color
      });
      
      updateUser(response.data);
      toast.success("Kategori eklendi");
      setIsDialogOpen(false);
      setNewCategory({ name: "", color: "#3B82F6" });
    } catch (error) {
      toast.error(error.response?.data?.detail || "Bir hata oluştu");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCategory = async (categoryId) => {
    if (!window.confirm("Bu kategoriyi silmek istediğinize emin misiniz?")) return;
    
    setDeletingId(categoryId);
    
    try {
      const response = await api.delete(`/users/${user.id}/categories/${categoryId}`);
      updateUser(response.data);
      toast.success("Kategori silindi");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Kategori silinemedi");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div>
        <h2 className="font-heading text-2xl font-bold">Ayarlar</h2>
        <p className="text-muted-foreground">Hesap ve uygulama ayarlarını yönetin</p>
      </div>

      {/* Profile Card */}
      <Card className="border-border/50 bg-card">
        <CardHeader>
          <CardTitle className="font-heading flex items-center gap-2">
            <User className="w-5 h-5 text-primary" />
            Profil Bilgileri
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
              <span className="text-primary font-heading text-2xl font-bold">
                {user?.name?.charAt(0).toUpperCase()}
              </span>
            </div>
            <div>
              <h3 className="font-heading text-lg font-bold">{user?.name}</h3>
              <p className="text-sm text-muted-foreground">Bu cihaza kayıtlı</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Categories Card */}
      <Card className="border-border/50 bg-card">
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="font-heading flex items-center gap-2">
              <Tag className="w-5 h-5 text-primary" />
              Kategoriler
            </CardTitle>
            <CardDescription>
              Görev kategorilerini yönetin
            </CardDescription>
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm" className="btn-glow" data-testid="add-category-btn">
                <Plus className="w-4 h-4 mr-2" />
                Yeni Kategori
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle className="font-heading">Yeni Kategori</DialogTitle>
                <DialogDescription>
                  Özel bir kategori oluşturun
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleAddCategory} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="categoryName">Kategori Adı</Label>
                  <Input
                    id="categoryName"
                    value={newCategory.name}
                    onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })}
                    placeholder="Örn: Manuel Test"
                    required
                    data-testid="category-name-input"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>Renk</Label>
                  <div className="flex flex-wrap gap-2">
                    {colorOptions.map((color) => (
                      <button
                        key={color}
                        type="button"
                        onClick={() => setNewCategory({ ...newCategory, color })}
                        className={cn(
                          "w-8 h-8 rounded-full transition-all",
                          newCategory.color === color && "ring-2 ring-offset-2 ring-offset-background ring-primary"
                        )}
                        style={{ backgroundColor: color }}
                        data-testid={`color-option-${color}`}
                      />
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-2 p-3 rounded-lg bg-secondary/30">
                  <Palette className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">Önizleme:</span>
                  <Badge style={{ backgroundColor: `${newCategory.color}20`, color: newCategory.color, borderColor: `${newCategory.color}30` }}>
                    {newCategory.name || "Kategori Adı"}
                  </Badge>
                </div>

                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                    İptal
                  </Button>
                  <Button type="submit" disabled={saving} data-testid="category-submit-btn">
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "Ekle"}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {user?.categories?.map((category) => (
              <div
                key={category.id}
                className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 border border-border/50"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: category.color }}
                  />
                  <span className="font-medium">{category.name}</span>
                  {category.is_default && (
                    <Badge variant="secondary" className="text-xs">Varsayılan</Badge>
                  )}
                </div>
                {!category.is_default && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive"
                    onClick={() => handleDeleteCategory(category.id)}
                    disabled={deletingId === category.id}
                    data-testid={`delete-category-${category.id}`}
                  >
                    {deletingId === category.id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </Button>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="border-destructive/50 bg-card">
        <CardHeader>
          <CardTitle className="font-heading text-destructive">Tehlikeli Bölge</CardTitle>
          <CardDescription>
            Bu işlemler geri alınamaz
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="destructive"
            onClick={logout}
            data-testid="logout-settings-btn"
          >
            Çıkış Yap
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default Settings;
