import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

interface AlimentoInventario {
  id: string
  nombre: string
  cantidadG: number
  prioridad: "alta" | "media" | "baja"
  grupo: string
  fechaLimite: string
}

// Datos de demostración basados en el inventario local para validar la renderización de la UI
const INVENTARIO_INICIAL: AlimentoInventario[] = [
  { id: "pollo_crudo", nombre: "Pollo Fresco", cantidadG: 2500, prioridad: "alta", grupo: "Proteína", fechaLimite: "2026-11-04" },
  { id: "carne_res_cruda", nombre: "Carne de Res Criolla", cantidadG: 1800, prioridad: "alta", grupo: "Proteína", fechaLimite: "2026-11-03" },
  { id: "name_diamante", nombre: "Ñame Diamante", cantidadG: 2000, prioridad: "media", grupo: "Tubérculo", fechaLimite: "2026-11-10" },
  { id: "tomate_perita", nombre: "Tomate Perita", cantidadG: 1400, prioridad: "alta", grupo: "Vegetal", fechaLimite: "2026-11-02" },
  { id: "culantro_fresco", nombre: "Culantro Fresco", cantidadG: 200, prioridad: "alta", grupo: "Vegetal", fechaLimite: "2026-11-02" },
]

export default function App() {
  const [filtro, setFiltro] = useState("")
  const [cargando, setCargando] = useState(false)

  const itemsFiltrados = INVENTARIO_INICIAL.filter((item) =>
    item.nombre.toLowerCase().includes(filtro.toLowerCase()) ||
    item.grupo.toLowerCase().includes(filtro.toLowerCase())
  )

  const toggleSimulacionCarga = () => {
    setCargando(true)
    setTimeout(() => setCargando(false), 800)
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Barra de navegación superior sobria y funcional */}
      <header className="border-b border-border bg-card/50 backdrop-blur px-6 py-3">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="h-3 w-3 rounded-full bg-primary" />
            <h1 className="text-base font-semibold tracking-tight">
              Gestor Nutricional & Despensa
            </h1>
            <Badge variant="outline" className="text-xs font-normal">
              shadcn/ui activo
            </Badge>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={toggleSimulacionCarga}
            disabled={cargando}
          >
            {cargando ? "Actualizando..." : "Simular carga"}
          </Button>
        </div>
      </header>

      {/* Contenido principal */}
      <main className="mx-auto max-w-6xl p-6 space-y-6">
        {/* Cabecera y buscador */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">Inventario de Ingredientes</h2>
            <p className="text-sm text-muted-foreground">
              Componentes shadcn configurados con Tailwind CSS v4 y tema neutro.
            </p>
          </div>
          <div className="w-full sm:w-72">
            <Input
              placeholder="Buscar por ingrediente o grupo..."
              value={filtro}
              onChange={(e) => setFiltro(e.target.value)}
              className="text-sm"
            />
          </div>
        </div>

        {/* Tabla de datos o Skeletons si está en estado de carga */}
        <Card className="border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium">Ingredientes Disponibles</CardTitle>
            <CardDescription className="text-xs">
              Listado con tipografía numérica tabular y etiquetas de prioridad.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {cargando ? (
              <div className="space-y-3 py-2">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            ) : itemsFiltrados.length === 0 ? (
              <div className="py-12 text-center text-sm text-muted-foreground">
                No se encontraron ingredientes con el término ingresado.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-border">
                    <TableHead>Ingrediente</TableHead>
                    <TableHead>Grupo</TableHead>
                    <TableHead className="text-right">Cantidad (g)</TableHead>
                    <TableHead>Prioridad</TableHead>
                    <TableHead className="text-right">Fecha Límite</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {itemsFiltrados.map((item) => (
                    <TableRow key={item.id} className="border-border">
                      <TableCell className="font-medium">{item.nombre}</TableCell>
                      <TableCell className="text-muted-foreground">{item.grupo}</TableCell>
                      <TableCell className="text-right font-mono tabular-nums">
                        {item.cantidadG.toLocaleString()} g
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            item.prioridad === "alta"
                              ? "destructive"
                              : item.prioridad === "media"
                              ? "secondary"
                              : "outline"
                          }
                          className="capitalize text-xs"
                        >
                          {item.prioridad}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs tabular-nums text-muted-foreground">
                        {item.fechaLimite}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
