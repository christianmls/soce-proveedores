# SOCE Pro - Sistema de Ofertas de Contratación

Sistema de gestión de ofertas de contratación pública construido con Next.js 15, Node 22, Prisma y Playwright.

## 🚀 Características

- **Gestión de Categorías**: Organiza proveedores y procesos por categorías
- **Base de Proveedores**: Mantén un registro de proveedores con su información
- **Procesos de Contratación**: Gestiona procesos de contratación pública
- **Web Scraping Automatizado**: Extrae ofertas automáticamente del portal de compras públicas
- **Interfaz Moderna**: UI construida con Tailwind CSS y Radix UI

## 📋 Requisitos Previos

- Node.js 22 o superior
- npm o yarn
- Docker (opcional, para deployment con contenedores)

## 🛠️ Instalación

### Desarrollo Local

1. **Clonar el repositorio**
```bash
cd soce-nextjs
```

2. **Instalar dependencias**
```bash
npm install
```

3. **Configurar variables de entorno**
```bash
cp .env.example .env
```

4. **Inicializar la base de datos**
```bash
npx prisma db push
npx prisma generate
```

5. **Instalar Playwright**
```bash
npx playwright install chromium --with-deps
```

6. **Ejecutar en modo desarrollo**
```bash
npm run dev
```

La aplicación estará disponible en [http://localhost:3000](http://localhost:3000)

### Deployment con Docker

1. **Construir la imagen**
```bash
docker-compose build
```

2. **Ejecutar el contenedor**
```bash
docker-compose up -d
```

## 📁 Estructura del Proyecto

```
soce-nextjs/
├── prisma/
│   └── schema.prisma          # Esquema de base de datos
├── src/
│   ├── app/
│   │   ├── actions/           # Server Actions
│   │   │   ├── categorias.ts
│   │   │   ├── proveedores.ts
│   │   │   ├── procesos.ts
│   │   │   └── scraping.ts
│   │   ├── categorias/        # Página de categorías
│   │   ├── proveedores/       # Página de proveedores
│   │   ├── procesos/          # Páginas de procesos
│   │   │   └── [id]/          # Detalle de proceso
│   │   ├── layout.tsx         # Layout principal
│   │   ├── page.tsx           # Página de inicio
│   │   └── globals.css        # Estilos globales
│   ├── components/
│   │   ├── ui/                # Componentes de UI base
│   │   ├── categorias/        # Componentes de categorías
│   │   ├── proveedores/       # Componentes de proveedores
│   │   ├── procesos/          # Componentes de procesos
│   │   └── sidebar.tsx        # Barra lateral de navegación
│   └── lib/
│       ├── prisma.ts          # Cliente de Prisma
│       ├── scraper.ts         # Lógica de scraping
│       └── utils.ts           # Utilidades
├── Dockerfile
├── docker-compose.yml
├── package.json
└── README.md
```

## 🗄️ Base de Datos

El proyecto usa SQLite con Prisma ORM. Los modelos principales son:

- **Categoria**: Categorías para organizar proveedores y procesos
- **Proveedor**: Información de proveedores
- **Proceso**: Procesos de contratación
- **Barrido**: Ejecuciones de scraping
- **Oferta**: Ofertas extraídas del portal
- **Anexo**: Documentos adjuntos a las ofertas

### Comandos útiles de Prisma

```bash
# Ver la base de datos en interfaz gráfica
npm run db:studio

# Actualizar esquema sin migraciones
npm run db:push

# Generar cliente de Prisma
npm run db:generate
```

## 🔍 Uso del Sistema

### 1. Crear Categorías
Primero crea categorías para organizar tus proveedores y procesos.

### 2. Agregar Proveedores
Agrega proveedores con su RUC y asígnalos a categorías.

### 3. Crear Procesos
Crea un proceso con el código del proceso de contratación pública.

### 4. Ejecutar Barrido
En el detalle del proceso, haz clic en "Iniciar Barrido" para extraer las ofertas automáticamente.

## 🔧 Scripts Disponibles

- `npm run dev` - Inicia el servidor de desarrollo
- `npm run build` - Construye la aplicación para producción
- `npm start` - Ejecuta la aplicación en modo producción
- `npm run lint` - Ejecuta el linter
- `npm run db:push` - Actualiza el esquema de la base de datos
- `npm run db:studio` - Abre Prisma Studio
- `npm run db:generate` - Genera el cliente de Prisma

## 🌐 Web Scraping

El sistema usa Playwright para extraer información del portal de compras públicas de Ecuador. El scraper extrae:

- Datos del proveedor (razón social, contacto, ubicación)
- Items de la oferta (descripción, cantidad, valores)
- Documentos anexos

El proceso de scraping se ejecuta de forma asíncrona y puede tomar varios minutos dependiendo del número de proveedores.

## 🔐 Seguridad

- Las Server Actions de Next.js se ejecutan en el servidor
- Validación de datos en formularios
- Sanitización de entradas del usuario

## 📝 Notas Técnicas

### Conversión de Python/Reflex a Next.js

Este proyecto es una conversión completa del proyecto original en Python/Reflex a Next.js:

- **State Management**: Convertido de Reflex State a React Server Components y Server Actions
- **UI Components**: Convertido de Reflex components a Radix UI + Tailwind CSS
- **Database**: Mantenido SQLite pero migrado de SQLModel a Prisma ORM
- **Scraping**: Convertido de Python Playwright a TypeScript Playwright
- **Routing**: Convertido a Next.js App Router

### Diferencias Clave

1. **Arquitectura**: De SSR tradicional (Reflex) a RSC (React Server Components)
2. **Estado**: De estado reactivo de Reflex a Server Actions con revalidación
3. **Tipos**: TypeScript proporciona type safety completo
4. **Performance**: Next.js optimiza automáticamente imágenes, fuentes y código

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT.

## 🐛 Reporte de Bugs

Si encuentras un bug, por favor abre un issue en GitHub con:
- Descripción del problema
- Pasos para reproducir
- Comportamiento esperado vs actual
- Screenshots si es aplicable
