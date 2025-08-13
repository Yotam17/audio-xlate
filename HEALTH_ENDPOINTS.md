# Health Check Endpoints

הפרויקט כולל מספר נתיבי health check לבדיקת מצב ה-API ולניטור:

## נתיבי Health Check זמינים

### 1. **`/health`** - Health Check מפורט
**שימוש**: בדיקה כללית של מצב המערכת
**תגובה**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000000",
  "service": "YT Xlate Agent API",
  "version": "1.0.0",
  "python_version": "3.9.0",
  "platform": "Linux-5.4.0-x86_64",
  "cpu_count": 8,
  "memory_total_gb": 16.0,
  "memory_available_gb": 8.5,
  "disk_usage_percent": 45.2,
  "environment": {
    "OPENAI_API_KEY": "SET",
    "ELEVENLABS_API_KEY": "SET"
  }
}
```

### 2. **`/health/simple`** - Health Check פשוט
**שימוש**: בדיקה מהירה ל-load balancers וניטור בסיסי
**תגובה**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

### 3. **`/health/detailed`** - Health Check מפורט מאוד
**שימוש**: בדיקה מעמיקה של כל השירותים והרכיבים
**תגובה**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000000",
  "service": "YT Xlate Agent API",
  "version": "1.0.0",
  "checks": {
    "environment": {
      "OPENAI_API_KEY": {
        "status": "SET",
        "description": "OpenAI API key for transcription and translation"
      },
      "ELEVENLABS_API_KEY": {
        "status": "SET",
        "description": "ElevenLabs API key for TTS generation"
      }
    },
    "file_system": {
      "status": "healthy",
      "message": "File system accessible"
    },
    "packages": {
      "fastapi": {
        "status": "healthy",
        "message": "Package available"
      },
      "openai": {
        "status": "healthy",
        "message": "Package available"
      }
    },
    "api_response": {
      "status": "healthy",
      "message": "API can generate responses"
    }
  }
}
```

### 4. **`/ready`** - Readiness Check
**שימוש**: בדיקה שהשירות מוכן לקבל traffic (Kubernetes)
**תגובה**:
```json
{
  "status": "ready",
  "timestamp": "2024-01-01T12:00:00.000000",
  "service": "YT Xlate Agent API",
  "checks": {
    "api_utils": {
      "status": "ready",
      "message": "API utilities available"
    },
    "tts_modules": {
      "status": "ready",
      "message": "TTS modules available"
    },
    "logic_modules": {
      "status": "ready",
      "message": "Logic modules available"
    }
  }
}
```

### 5. **`/startup`** - Startup Check
**שימוש**: בדיקה שהשירות סיים להתחיל (Kubernetes)
**תגובה**:
```json
{
  "status": "started",
  "timestamp": "2024-01-01T12:00:00.000000",
  "service": "YT Xlate Agent API",
  "version": "1.0.0",
  "startup_time": "immediate",
  "checks": {
    "main_app": {
      "status": "started",
      "message": "FastAPI application is running"
    },
    "routers": {
      "translate": {
        "status": "started",
        "message": "Router translate included"
      },
      "tts": {
        "status": "started",
        "message": "Router tts included"
      }
    }
  }
}
```

## שימוש ב-Kubernetes

### Health Check
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

### Readiness Check
```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Startup Check
```yaml
startupProbe:
  httpGet:
    path: /startup
    port: 8000
  initialDelaySeconds: 1
  periodSeconds: 2
  failureThreshold: 30
```

## שימוש ב-Load Balancers

### Nginx
```nginx
location /health {
    proxy_pass http://backend/health;
    access_log off;
}
```

### HAProxy
```
option httpchk GET /health
http-check expect status 200
```

## ניטור וכלים

### Prometheus
ניתן להשתמש ב-`/health/detailed` כדי לחלץ metrics:
- מצב משתני הסביבה
- זמינות הרכיבים
- מצב מערכת הקבצים

### Grafana
יצירת dashboards המבוססים על נתוני ה-health check

### Alerting
הגדרת התראות כאשר:
- `status` הוא `unhealthy`
- `status` הוא `not_ready`
- `status` הוא `not_started`

## דוגמאות לשימוש

### בדיקה מהירה
```bash
curl http://localhost:8000/health/simple
```

### בדיקה מפורטת
```bash
curl http://localhost:8000/health/detailed
```

### בדיקת מוכנות
```bash
curl http://localhost:8000/ready
```

### בדיקת הפעלה
```bash
curl http://localhost:8000/startup
```

## הערות חשובות

1. **ביצועים**: כל הבדיקות מהירות ואינן משפיעות על ביצועי ה-API
2. **אבטחה**: הנתיבים לא חושפים מידע רגיש
3. **זמינות**: הנתיבים תמיד זמינים גם אם יש בעיות ב-API הראשי
4. **לוגים**: מומלץ לרשום את כל הבדיקות ל-logs לניטור
