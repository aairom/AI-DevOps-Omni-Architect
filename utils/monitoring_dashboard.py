"""
Advanced Monitoring Dashboard for Omni-Architect
Provides real-time metrics, performance tracking, and system health monitoring
"""
import asyncio
import time
import psutil
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System-level metrics"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_requests: int = 0
    cache_hit_rate: float = 0.0
    avg_response_time: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0
    uptime_seconds: float = 0.0


@dataclass
class AIProviderMetrics:
    """AI Provider-specific metrics"""
    provider_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    total_tokens: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    last_request_time: Optional[datetime] = None


class MonitoringDashboard:
    """
    Advanced monitoring dashboard with real-time metrics tracking
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize monitoring dashboard
        
        Args:
            max_history: Maximum number of historical data points to keep
        """
        self.max_history = max_history
        self.start_time = datetime.now()
        
        # Metric storage
        self.response_times: deque = deque(maxlen=max_history)
        self.request_timestamps: deque = deque(maxlen=max_history)
        self.error_log: deque = deque(maxlen=100)
        
        # Provider metrics
        self.provider_metrics: Dict[str, AIProviderMetrics] = {}
        
        # System metrics
        self.system_metrics = SystemMetrics()
        
        # Performance tracking
        self.active_requests = 0
        self._lock = asyncio.Lock()
        
        logger.info("Monitoring dashboard initialized")
    
    async def record_request_start(self, provider: str) -> str:
        """
        Record the start of a request
        
        Args:
            provider: AI provider name
            
        Returns:
            Request ID for tracking
        """
        async with self._lock:
            request_id = f"{provider}_{int(time.time() * 1000)}"
            self.active_requests += 1
            self.request_timestamps.append(datetime.now())
            
            # Initialize provider metrics if needed
            if provider not in self.provider_metrics:
                self.provider_metrics[provider] = AIProviderMetrics(provider_name=provider)
            
            self.provider_metrics[provider].total_requests += 1
            self.system_metrics.total_requests += 1
            
            return request_id
    
    async def record_request_end(
        self, 
        provider: str, 
        request_id: str, 
        success: bool, 
        response_time: float,
        tokens: int = 0,
        cached: bool = False
    ):
        """
        Record the end of a request
        
        Args:
            provider: AI provider name
            request_id: Request tracking ID
            success: Whether request was successful
            response_time: Response time in seconds
            tokens: Number of tokens used
            cached: Whether response was from cache
        """
        async with self._lock:
            self.active_requests = max(0, self.active_requests - 1)
            self.response_times.append(response_time)
            
            if provider in self.provider_metrics:
                metrics = self.provider_metrics[provider]
                
                if success:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
                    self.system_metrics.failed_requests += 1
                
                # Update average response time
                total = metrics.successful_requests + metrics.failed_requests
                metrics.avg_response_time = (
                    (metrics.avg_response_time * (total - 1) + response_time) / total
                )
                
                metrics.total_tokens += tokens
                metrics.last_request_time = datetime.now()
                
                if cached:
                    metrics.cache_hits += 1
                else:
                    metrics.cache_misses += 1
    
    async def record_error(self, provider: str, error: str):
        """
        Record an error
        
        Args:
            provider: AI provider name
            error: Error message
        """
        async with self._lock:
            self.error_log.append({
                'timestamp': datetime.now(),
                'provider': provider,
                'error': error
            })
            logger.error(f"Error recorded for {provider}: {error}")
    
    def get_system_metrics(self) -> SystemMetrics:
        """
        Get current system metrics
        
        Returns:
            SystemMetrics object
        """
        # Update system metrics
        self.system_metrics.cpu_usage = psutil.cpu_percent(interval=0.1)
        self.system_metrics.memory_usage = psutil.virtual_memory().percent
        self.system_metrics.active_requests = self.active_requests
        
        # Calculate average response time
        if self.response_times:
            self.system_metrics.avg_response_time = sum(self.response_times) / len(self.response_times)
        
        # Calculate cache hit rate
        total_cache_ops = sum(
            m.cache_hits + m.cache_misses 
            for m in self.provider_metrics.values()
        )
        if total_cache_ops > 0:
            total_hits = sum(m.cache_hits for m in self.provider_metrics.values())
            self.system_metrics.cache_hit_rate = (total_hits / total_cache_ops) * 100
        
        # Calculate uptime
        self.system_metrics.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        return self.system_metrics
    
    def get_provider_metrics(self, provider: Optional[str] = None) -> Dict[str, AIProviderMetrics]:
        """
        Get provider-specific metrics
        
        Args:
            provider: Specific provider name, or None for all providers
            
        Returns:
            Dictionary of provider metrics
        """
        if provider:
            return {provider: self.provider_metrics.get(provider, AIProviderMetrics(provider_name=provider))}
        return self.provider_metrics.copy()
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent errors
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of recent errors
        """
        return list(self.error_log)[-limit:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive performance statistics
        
        Returns:
            Dictionary of performance stats
        """
        response_times_list = list(self.response_times)
        
        stats = {
            'total_requests': self.system_metrics.total_requests,
            'successful_requests': sum(m.successful_requests for m in self.provider_metrics.values()),
            'failed_requests': self.system_metrics.failed_requests,
            'active_requests': self.active_requests,
            'avg_response_time': self.system_metrics.avg_response_time,
            'cache_hit_rate': self.system_metrics.cache_hit_rate,
            'uptime_hours': self.system_metrics.uptime_seconds / 3600,
        }
        
        if response_times_list:
            sorted_times = sorted(response_times_list)
            stats.update({
                'min_response_time': min(response_times_list),
                'max_response_time': max(response_times_list),
                'p50_response_time': sorted_times[len(sorted_times) // 2],
                'p95_response_time': sorted_times[int(len(sorted_times) * 0.95)],
                'p99_response_time': sorted_times[int(len(sorted_times) * 0.99)],
            })
        
        return stats
    
    def get_request_rate(self, window_seconds: int = 60) -> float:
        """
        Calculate request rate over a time window
        
        Args:
            window_seconds: Time window in seconds
            
        Returns:
            Requests per second
        """
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
        recent_requests = sum(1 for ts in self.request_timestamps if ts > cutoff_time)
        return recent_requests / window_seconds if window_seconds > 0 else 0.0
    
    def get_health_status(self) -> Tuple[str, Dict[str, Any]]:
        """
        Get overall system health status
        
        Returns:
            Tuple of (status, details) where status is 'healthy', 'degraded', or 'unhealthy'
        """
        metrics = self.get_system_metrics()
        stats = self.get_performance_stats()
        
        issues = []
        status = 'healthy'
        
        # Check CPU usage
        if metrics.cpu_usage > 90:
            issues.append('High CPU usage')
            status = 'degraded'
        
        # Check memory usage
        if metrics.memory_usage > 90:
            issues.append('High memory usage')
            status = 'degraded'
        
        # Check error rate
        if stats['total_requests'] > 0:
            error_rate = (stats['failed_requests'] / stats['total_requests']) * 100
            if error_rate > 10:
                issues.append(f'High error rate: {error_rate:.1f}%')
                status = 'unhealthy' if error_rate > 25 else 'degraded'
        
        # Check response time
        if stats.get('avg_response_time', 0) > 30:
            issues.append('Slow response times')
            status = 'degraded'
        
        # Check cache performance
        if stats.get('cache_hit_rate', 0) < 20 and stats['total_requests'] > 10:
            issues.append('Low cache hit rate')
        
        details = {
            'status': status,
            'issues': issues,
            'metrics': {
                'cpu_usage': metrics.cpu_usage,
                'memory_usage': metrics.memory_usage,
                'error_rate': (stats['failed_requests'] / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0,
                'avg_response_time': stats.get('avg_response_time', 0),
                'cache_hit_rate': stats.get('cache_hit_rate', 0),
            }
        }
        
        return status, details
    
    async def reset_metrics(self):
        """Reset all metrics"""
        async with self._lock:
            self.response_times.clear()
            self.request_timestamps.clear()
            self.error_log.clear()
            self.provider_metrics.clear()
            self.system_metrics = SystemMetrics()
            self.active_requests = 0
            self.start_time = datetime.now()
            logger.info("Monitoring metrics reset")
    
    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all metrics for external monitoring systems
        
        Returns:
            Dictionary of all metrics
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': {
                'cpu_usage': self.system_metrics.cpu_usage,
                'memory_usage': self.system_metrics.memory_usage,
                'active_requests': self.system_metrics.active_requests,
                'cache_hit_rate': self.system_metrics.cache_hit_rate,
                'avg_response_time': self.system_metrics.avg_response_time,
                'total_requests': self.system_metrics.total_requests,
                'failed_requests': self.system_metrics.failed_requests,
                'uptime_seconds': self.system_metrics.uptime_seconds,
            },
            'provider_metrics': {
                name: {
                    'total_requests': m.total_requests,
                    'successful_requests': m.successful_requests,
                    'failed_requests': m.failed_requests,
                    'avg_response_time': m.avg_response_time,
                    'total_tokens': m.total_tokens,
                    'cache_hits': m.cache_hits,
                    'cache_misses': m.cache_misses,
                    'last_request_time': m.last_request_time.isoformat() if m.last_request_time else None,
                }
                for name, m in self.provider_metrics.items()
            },
            'performance_stats': self.get_performance_stats(),
            'health_status': self.get_health_status()[1],
        }


# Global monitoring dashboard instance
monitoring_dashboard = MonitoringDashboard()

# Made with Bob
