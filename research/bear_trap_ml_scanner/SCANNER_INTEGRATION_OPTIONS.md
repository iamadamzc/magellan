# Scanner-Strategy Integration Options

> **Status**: Scanners and strategy are currently separate  
> **Next Step**: Choose integration approach  
> **Created**: January 22, 2026

---

## 🎯 Current State

### **Scanner** (Standalone)
```
Location: research/bear_trap_ml_scanner/scanner/
Status: ✅ Complete and functional
Outputs: Console alerts + JSON files
Runs: Independently via websocket_runner.py
```

### **Strategy** (Standalone)
```
Location: test/midday_reversion/
Status: ✅ Complete but not trading yet
Inputs: Polls its own 50 symbols
Runs: Independently via runner.py
```

**They don't communicate yet.**

---

## 🔌 Integration Option 1: File-Based Alert System

### **Architecture**
```
Scanner (WebSocket)
   ↓ Writes
JSON Alert Files
   ↓ Reads
Strategy (Polling)
   ↓ Executes
Trades
```

### **How It Works**
1. Scanner runs continuously (WebSocket)
2. Detects selloffs, writes to `alerts/alerts_YYYY-MM-DD.json`
3. Strategy polls alert file every 10 seconds
4. Strategy reads new HIGH priority alerts
5. Strategy executes trades

### **Implementation**
```python
# In test/midday_reversion/strategy.py

class MiddayReversionStrategy:
    def __init__(self):
        self.alert_file_pattern = "research/bear_trap_ml_scanner/scanner/alerts/alerts_*.json"
        self.processed_alerts = set()
    
    def check_scanner_alerts(self):
        """Check for new scanner alerts"""
        today = datetime.now().strftime("%Y-%m-%d")
        alert_file = f"research/bear_trap_ml_scanner/scanner/alerts/alerts_{today}.json"
        
        if not os.path.exists(alert_file):
            return []
        
        with open(alert_file) as f:
            alerts = json.load(f)
        
        # Filter for HIGH priority, unprocessed
        new_alerts = [
            a for a in alerts
            if a['score']['tier'] == 'HIGH'
            and a['timestamp'] not in self.processed_alerts
        ]
        
        return new_alerts
    
    def process_scanner_alert(self, alert):
        """Process a scanner alert"""
        symbol = alert['event']['symbol']
        drop_pct = alert['event']['drop_pct']
        score = alert['score']['total_score']
        
        # Validate and execute
        if self._validate_entry(symbol):
            self._enter_position(symbol, alert)
            self.processed_alerts.add(alert['timestamp'])
```

### **Pros**
- ✅ Simple to implement
- ✅ Decoupled (scanner/strategy run independently)
- ✅ Easy to debug (can inspect JSON files)
- ✅ No shared state

### **Cons**
- ⚠️ Slight delay (polling interval)
- ⚠️ File I/O overhead
- ⚠️ Need to manage processed alerts

### **Best For**
- Initial integration
- Testing and validation
- Simple deployments

---

## 🔌 Integration Option 2: Direct Callback System

### **Architecture**
```
Strategy
   ↓ Imports
WebSocketScanner
   ↓ Callback on detect
Strategy.handle_selloff()
   ↓ Executes
Trades
```

### **How It Works**
1. Strategy imports and initializes WebSocketScanner
2. Scanner calls strategy callback on selloff detection
3. Strategy immediately evaluates and executes
4. Tightly coupled, instant execution

### **Implementation**
```python
# In test/midday_reversion/strategy.py

from research.bear_trap_ml_scanner.scanner import WebSocketScanner

class MiddayReversionStrategy:
    def __init__(self, api_key, api_secret, symbols, config):
        # ... existing init ...
        
        # Initialize scanner with callback
        self.scanner = WebSocketScanner(
            api_key=api_key,
            api_secret=api_secret,
            symbols=symbols,
            threshold_pct=-10.0,
            time_filter=(11, 30, 14, 0),
        )
        
        # Register callback
        self.scanner.on_selloff = self.handle_scanner_selloff
    
    def handle_scanner_selloff(self, event, score_data):
        """Called by scanner when selloff detected"""
        if score_data['tier'] != 'HIGH':
            return  # Only trade HIGH priority
        
        symbol = event.symbol
        
        # Check if we can trade
        if not self._check_risk_gates(symbol):
            return
        
        # Execute entry
        self._enter_position_from_scanner(symbol, event, score_data)
    
    async def run(self):
        """Run strategy with integrated scanner"""
        # Start scanner in background
        await self.scanner.run()
```

### **Pros**
- ✅ Instant execution (no polling delay)
- ✅ Single process (simpler deployment)
- ✅ Shared state (scanner knows strategy status)
- ✅ Efficient (no file I/O)

### **Cons**
- ⚠️ Tightly coupled (harder to debug)
- ⚠️ Need async/await handling
- ⚠️ Scanner failure = strategy failure

### **Best For**
- Production deployment
- Low-latency requirements
- Single-service architecture

---

## 🔌 Integration Option 3: Message Queue (Production)

### **Architecture**
```
Scanner Service
   ↓ Publishes
Message Queue (Redis/RabbitMQ)
   ↓ Subscribes
Strategy Service
   ↓ Executes
Trades
```

### **How It Works**
1. Scanner runs as separate service
2. Publishes alerts to message queue
3. Strategy subscribes to queue
4. Multiple strategies can consume same alerts
5. Fully decoupled, scalable

### **Implementation**
```python
# Scanner side
import redis

class WebSocketScanner:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def _handle_selloff(self, event, score_data):
        # Publish to Redis
        alert = {
            'event': event.to_dict(),
            'score': score_data,
        }
        self.redis.publish('selloff_alerts', json.dumps(alert))

# Strategy side
class MiddayReversionStrategy:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.pubsub = redis_client.pubsub()
        self.pubsub.subscribe('selloff_alerts')
    
    def listen_for_alerts(self):
        """Listen for scanner alerts"""
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                alert = json.loads(message['data'])
                self.process_alert(alert)
```

### **Pros**
- ✅ Fully decoupled (services independent)
- ✅ Scalable (multiple consumers)
- ✅ Reliable (queue persistence)
- ✅ Production-grade

### **Cons**
- ⚠️ Requires message queue infrastructure
- ⚠️ More complex setup
- ⚠️ Additional dependency

### **Best For**
- Production at scale
- Multiple strategies
- Microservices architecture

---

## 🎯 Recommended Approach

### **Phase 1: File-Based (Now)**
- Quick to implement
- Easy to test
- Validate the workflow

### **Phase 2: Direct Callback (Soon)**
- Once validated
- For production
- Better performance

### **Phase 3: Message Queue (Future)**
- If scaling to multiple strategies
- If deploying to multiple servers
- Enterprise-grade

---

## 🔧 Implementation Checklist

### **Option 1: File-Based**
- [ ] Add alert reader to strategy
- [ ] Add processed alert tracking
- [ ] Add validation logic
- [ ] Test with live scanner
- [ ] Monitor for 1 week

### **Option 2: Direct Callback**
- [ ] Modify scanner to support callbacks
- [ ] Integrate scanner into strategy
- [ ] Handle async/await
- [ ] Add error handling
- [ ] Test with live market

### **Option 3: Message Queue**
- [ ] Set up Redis/RabbitMQ
- [ ] Add publisher to scanner
- [ ] Add subscriber to strategy
- [ ] Handle reconnection
- [ ] Monitor queue health

---

## 📊 Comparison Matrix

| Feature | File-Based | Callback | Message Queue |
|---------|------------|----------|---------------|
| **Complexity** | Low | Medium | High |
| **Latency** | ~10 sec | <1 sec | ~1 sec |
| **Coupling** | Loose | Tight | Loose |
| **Scalability** | Low | Medium | High |
| **Reliability** | Medium | Medium | High |
| **Setup Time** | 15 min | 30 min | 2 hours |
| **Best For** | Testing | Production | Enterprise |

---

## 💡 Next Steps

1. **Choose integration approach** based on needs
2. **Implement chosen option**
3. **Test with live scanner** tomorrow (9:30 AM ET)
4. **Validate** alert quality and execution
5. **Monitor** for 1 week before going live

---

## 📝 Notes

- Scanner is ready to use standalone
- Strategy is ready to use standalone
- Integration is optional but recommended
- Start simple (file-based), upgrade later

---

*Integration options documented: January 22, 2026*  
*Ready for implementation when needed*
