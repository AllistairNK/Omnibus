import { Component, OnInit, OnDestroy, ElementRef, ViewChild, Input, AfterViewInit, NgZone } from '@angular/core';

@Component({
  selector: 'app-digital-rain',
  templateUrl: './digital-rain.component.html',
  styleUrls: ['./digital-rain.component.scss']
})
export class DigitalRainComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('canvas', { static: true }) canvasRef!: ElementRef<HTMLCanvasElement>;
  @Input() speed: number = 5;
  @Input() density: number = 50;
  @Input() characterSet: string = '01';
  @Input() fontSize: number = 14;
  @Input() color: string = '#0f0';
  @Input() trailLength: number = 20;
  @Input() fadeSpeed: number = 0.05;

  private ctx!: CanvasRenderingContext2D;
  private animationId: number = 0;
  private columns: number = 0;
  private drops: number[] = [];
  private characters: string[] = [];
  private lastTime: number = 0;
  private isActive: boolean = false;
  private resizeObserver: ResizeObserver | null = null;

  constructor(private ngZone: NgZone) {}

  ngOnInit(): void {
    this.characters = this.characterSet.split('');
  }

  ngAfterViewInit(): void {
    this.initCanvas();
    this.startAnimation();
    this.setupResizeObserver();
  }

  ngOnDestroy(): void {
    this.stopAnimation();
    this.cleanupResizeObserver();
  }

  private initCanvas(): void {
    const canvas = this.canvasRef.nativeElement;
    const container = canvas.parentElement;
    
    if (container) {
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
    } else {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }

    this.ctx = canvas.getContext('2d')!;
    this.ctx.font = `${this.fontSize}px 'Courier New', monospace`;
    
    // Calculate columns based on font size
    this.columns = Math.floor(canvas.width / this.fontSize);
    
    // Initialize drops
    this.drops = [];
    for (let i = 0; i < this.columns; i++) {
      this.drops[i] = Math.random() * -100; // Start at random positions above canvas
    }
  }

  private startAnimation(): void {
    this.isActive = true;
    this.lastTime = performance.now();
    
    // Run outside Angular zone for better performance
    this.ngZone.runOutsideAngular(() => {
      const animate = (currentTime: number) => {
        if (!this.isActive) return;
        
        const deltaTime = currentTime - this.lastTime;
        this.lastTime = currentTime;
        
        this.update(deltaTime);
        this.draw();
        
        this.animationId = requestAnimationFrame(animate);
      };
      
      this.animationId = requestAnimationFrame(animate);
    });
  }

  private stopAnimation(): void {
    this.isActive = false;
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }
  }

  private update(deltaTime: number): void {
    const canvas = this.canvasRef.nativeElement;
    const timeFactor = deltaTime / 16; // Normalize to 60fps
    
    for (let i = 0; i < this.columns; i++) {
      // Randomly reset drops
      if (this.drops[i] * this.fontSize > canvas.height && Math.random() > 0.975) {
        this.drops[i] = 0;
      }
      
      // Move drops
      this.drops[i] += (this.speed / 10) * timeFactor;
    }
  }

  private draw(): void {
    const canvas = this.canvasRef.nativeElement;
    const ctx = this.ctx;
    
    // Semi-transparent black rectangle for trail effect
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw characters
    ctx.fillStyle = this.color;
    
    for (let i = 0; i < this.columns; i++) {
      if (Math.random() > this.density / 100) continue;
      
      const x = i * this.fontSize;
      const y = this.drops[i] * this.fontSize;
      
      // Draw main character
      const char = this.characters[Math.floor(Math.random() * this.characters.length)];
      ctx.fillText(char, x, y);
      
      // Draw trail characters with fading opacity
      for (let j = 1; j < this.trailLength; j++) {
        const trailY = y - j * this.fontSize;
        if (trailY < 0) break;
        
        const opacity = 1 - (j / this.trailLength);
        ctx.fillStyle = `rgba(0, 255, 0, ${opacity * 0.7})`;
        
        const trailChar = this.characters[Math.floor(Math.random() * this.characters.length)];
        ctx.fillText(trailChar, x, trailY);
      }
      
      // Reset fill style for next column
      ctx.fillStyle = this.color;
    }
  }

  @Input() set active(value: boolean) {
    if (value && !this.isActive) {
      this.initCanvas();
      this.startAnimation();
    } else if (!value && this.isActive) {
      this.stopAnimation();
    }
  }

  // Handle window resize
  onResize(): void {
    this.initCanvas();
  }

  private setupResizeObserver(): void {
    if (typeof ResizeObserver !== 'undefined') {
      const container = this.canvasRef.nativeElement.parentElement;
      if (container) {
        this.resizeObserver = new ResizeObserver(() => {
          this.initCanvas();
        });
        this.resizeObserver.observe(container);
      }
    } else {
      // Fallback to window resize event
      window.addEventListener('resize', this.onResize.bind(this));
    }
  }

  private cleanupResizeObserver(): void {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
      this.resizeObserver = null;
    } else {
      window.removeEventListener('resize', this.onResize.bind(this));
    }
  }
}
