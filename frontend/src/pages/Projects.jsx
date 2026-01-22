import { useEffect, useState } from "react";
import api from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { toast } from "sonner";
import { 
  Plus, 
  FolderKanban,
  MoreVertical,
  Edit,
  Trash2,
  Loader2,
  CheckSquare
} from "lucide-react";
import { cn } from "../lib/utils";
import { format } from "date-fns";
import { tr } from "date-fns/locale";

const Projects = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [saving, setSaving] = useState(false);
  
  const [formData, setFormData] = useState({
    name: "",
    description: ""
  });

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await api.get("/projects");
      setProjects(response.data);
    } catch (error) {
      toast.error("Projeler yüklenirken hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      if (editingProject) {
        await api.put(`/projects/${editingProject.id}`, formData);
        toast.success("Proje güncellendi");
      } else {
        await api.post("/projects", formData);
        toast.success("Proje oluşturuldu");
      }
      
      setIsDialogOpen(false);
      resetForm();
      fetchProjects();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Bir hata oluştu");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (project) => {
    setEditingProject(project);
    setFormData({
      name: project.name,
      description: project.description || ""
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (projectId) => {
    if (!window.confirm("Bu projeyi ve içindeki tüm görevleri silmek istediğinize emin misiniz?")) return;
    
    try {
      await api.delete(`/projects/${projectId}`);
      toast.success("Proje silindi");
      fetchProjects();
    } catch (error) {
      toast.error("Proje silinirken hata oluştu");
    }
  };

  const resetForm = () => {
    setEditingProject(null);
    setFormData({ name: "", description: "" });
  };

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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="font-heading text-2xl font-bold">Projeler</h2>
          <p className="text-muted-foreground">{projects.length} proje</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={(open) => {
          setIsDialogOpen(open);
          if (!open) resetForm();
        }}>
          <DialogTrigger asChild>
            <Button className="btn-glow" data-testid="new-project-btn">
              <Plus className="w-4 h-4 mr-2" />
              Yeni Proje
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="font-heading">
                {editingProject ? "Projeyi Düzenle" : "Yeni Proje"}
              </DialogTitle>
              <DialogDescription>
                Proje detaylarını girin
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Proje Adı</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Proje adı"
                  required
                  data-testid="project-name-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Açıklama</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Proje açıklaması (opsiyonel)"
                  rows={3}
                  data-testid="project-description-input"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  İptal
                </Button>
                <Button type="submit" disabled={saving} data-testid="project-submit-btn">
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : (editingProject ? "Güncelle" : "Oluştur")}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.length > 0 ? (
          projects.map((project, index) => (
            <Card 
              key={project.id} 
              className={cn(
                "card-hover border-border/50 bg-card animate-slideIn",
                `stagger-${(index % 5) + 1}`
              )}
              style={{ animationFillMode: "both" }}
            >
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                    <FolderKanban className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="font-heading text-base">{project.name}</CardTitle>
                    <p className="text-xs text-muted-foreground font-mono">
                      {format(new Date(project.created_at), "d MMM yyyy", { locale: tr })}
                    </p>
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8" data-testid={`project-menu-${project.id}`}>
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => handleEdit(project)} data-testid={`project-edit-${project.id}`}>
                      <Edit className="w-4 h-4 mr-2" />
                      Düzenle
                    </DropdownMenuItem>
                    <DropdownMenuItem 
                      onClick={() => handleDelete(project.id)} 
                      className="text-destructive"
                      data-testid={`project-delete-${project.id}`}
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Sil
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </CardHeader>
              <CardContent>
                {project.description && (
                  <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                    {project.description}
                  </p>
                )}
                <div className="flex items-center gap-2">
                  <CheckSquare className="w-4 h-4 text-muted-foreground" />
                  <Badge variant="secondary" className="font-mono">
                    {project.task_count} görev
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <Card className="col-span-full border-border/50 bg-card">
            <CardContent className="p-8 text-center">
              <FolderKanban className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
              <p className="text-muted-foreground">
                Henüz proje yok. İlk projenizi oluşturun!
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Projects;
