import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, interval, Subscription, combineLatest } from 'rxjs';
import { map, take } from 'rxjs/operators';

export type EmotionType = 
  | 'neutral' 
  | 'happy' 
  | 'thinking' 
  | 'confused' 
  | 'excited' 
  | 'sad' 
  | 'loading' 
  | 'success' 
  | 'error';

export interface EmotionState {
  currentEmotion: EmotionType;
  previousEmotion: EmotionType | null;
  transitionProgress: number; // 0 to 1
  isTransitioning: boolean;
}

export interface AsciiArt {
  frames: string[];
  frameRate: number; // ms per frame
  loop: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AsciiEmotionService {
  private emotionLibrary: Map<EmotionType, AsciiArt> = new Map();
  private currentEmotionSubject = new BehaviorSubject<EmotionType>('neutral');
  private emotionStateSubject = new BehaviorSubject<EmotionState>({
    currentEmotion: 'neutral',
    previousEmotion: null,
    transitionProgress: 0,
    isTransitioning: false
  });
  
  private activeAnimation: Subscription | null = null;
  private transitionInterval: Subscription | null = null;
  private currentFrameIndex = 0;
  private frameIndexSubject = new BehaviorSubject<number>(0);
  private animationRunningSubject = new BehaviorSubject<boolean>(true);

  constructor() {
    this.initializeEmotionLibrary();
    // Start animation for initial neutral emotion
    setTimeout(() => this.startAnimation(), 100);
  }

  /**
   * Initialize the ASCII emotion library with various emotions
   */
  private initializeEmotionLibrary(): void {
    // Neutral emotion (default)
    this.emotionLibrary.set('neutral', {
      frames: [
        `
        ( •_•)
        `
      ],
      frameRate: 1000,
      loop: false
    });

    // Happy emotion
    this.emotionLibrary.set('happy', {
      frames: [
        `
        (^_^)
        `,
        `
        (^_^)b
        `,
        `
        (^_^)/
        `
      ],
      frameRate: 300,
      loop: true
    });

    // Thinking emotion
    this.emotionLibrary.set('thinking', {
      frames: [
        `
        (•_•)
        `,
        `
        (•_•)⌐■-■
        `,
        `
        (⌐■_■)  
        `
      ],
      frameRate: 500,
      loop: true
    });

    // Confused emotion
    this.emotionLibrary.set('confused', {
      frames: [
        `
        (⊙_☉)
        `,
        `
        (⊙_☉)?
        `,
        `
        (⊙_☉)???
        `
      ],
      frameRate: 400,
      loop: true
    });

    // Excited emotion
    this.emotionLibrary.set('excited', {
      frames: [
        `
        (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧
        `,
        `
        (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ ✧ﾟ･: *ヽ(◕ヮ◕ヽ)
        `,
        `
        (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧
        `
      ],
      frameRate: 200,
      loop: true
    });

    // Sad emotion
    this.emotionLibrary.set('sad', {
      frames: [
        `
        (︶︹︶)
        `,
        `
        (︶︹︶)...
        `,
        `
        (︶︹︶)....
        `
      ],
      frameRate: 600,
      loop: true
    });

    // Loading emotion (spinner)
    this.emotionLibrary.set('loading', {
      frames: [
        '⠋ Loading',
        '⠙ Loading',
        '⠹ Loading',
        '⠸ Loading',
        '⠼ Loading',
        '⠴ Loading',
        '⠦ Loading',
        '⠧ Loading',
        '⠇ Loading',
        '⠏ Loading'
      ],
      frameRate: 100,
      loop: true
    });

    // Success emotion
    this.emotionLibrary.set('success', {
      frames: [
        `
        (•̀ᴗ•́)و ̑̑
        `,
        `
        (•̀ᴗ•́)و ̑̑ ✓
        `,
        `
        (•̀ᴗ•́)و ̑̑ ✓ Done!
        `
      ],
      frameRate: 500,
      loop: true
    });

    // Error emotion
    this.emotionLibrary.set('error', {
      frames: [
        `
        (×_×)
        `,
        `
        (×_×)⌐■-■
        `,
        `
        (⌐■_■) Error!
        `
      ],
      frameRate: 500,
      loop: true
    });
  }

  /**
   * Get the current emotion
   */
  getCurrentEmotion(): Observable<EmotionType> {
    return this.currentEmotionSubject.asObservable();
  }

  /**
   * Get the current emotion state
   */
  getEmotionState(): Observable<EmotionState> {
    return this.emotionStateSubject.asObservable();
  }

  /**
   * Get animation running state
   */
  isAnimationRunning(): Observable<boolean> {
    return this.animationRunningSubject.asObservable();
  }

  /**
   * Toggle animation on/off
   */
  toggleAnimation(): void {
    if (this.animationRunningSubject.value) {
      this.stopAnimation();
    } else {
      this.startAnimation();
    }
  }

  /**
   * Pause animation (alias for stopAnimation)
   */
  pauseAnimation(): void {
    this.stopAnimation();
  }

  /**
   * Resume animation (alias for startAnimation)
   */
  resumeAnimation(): void {
    this.startAnimation();
  }

  /**
   * Set a new emotion with optional transition
   */
  setEmotion(emotion: EmotionType, transitionDuration: number = 500): void {
    const currentState = this.emotionStateSubject.value;
    
    if (currentState.currentEmotion === emotion) {
      return;
    }

    // Stop any ongoing transition
    if (this.transitionInterval) {
      this.transitionInterval.unsubscribe();
    }

    // Update state to start transition
    this.emotionStateSubject.next({
      currentEmotion: emotion,
      previousEmotion: currentState.currentEmotion,
      transitionProgress: 0,
      isTransitioning: true
    });

    // Animate the transition
    const steps = 20;
    const stepDuration = transitionDuration / steps;
    let progress = 0;

    this.transitionInterval = interval(stepDuration).pipe(
      take(steps)
    ).subscribe({
      next: () => {
        progress += 1 / steps;
        this.emotionStateSubject.next({
          currentEmotion: emotion,
          previousEmotion: currentState.currentEmotion,
          transitionProgress: progress,
          isTransitioning: progress < 1
        });
      },
      complete: () => {
        // Transition complete
        this.emotionStateSubject.next({
          currentEmotion: emotion,
          previousEmotion: currentState.currentEmotion,
          transitionProgress: 1,
          isTransitioning: false
        });
        this.currentEmotionSubject.next(emotion);
        // Start animation for the new emotion if it has multiple frames
        this.startAnimation();
      }
    });
  }

  /**
   * Get ASCII art for a specific emotion
   */
  getAsciiArt(emotion: EmotionType): AsciiArt | undefined {
    return this.emotionLibrary.get(emotion);
  }

  /**
   * Get current frame of ASCII art for the current emotion
   */
  getCurrentFrame(): Observable<string> {
    return combineLatest([
      this.getEmotionState(),
      this.frameIndexSubject
    ]).pipe(
      map(([state, frameIndex]) => {
        const art = this.emotionLibrary.get(state.currentEmotion);
        if (!art || art.frames.length === 0) {
          return '';
        }
        
        // If transitioning, blend between previous and current frames
        if (state.isTransitioning && state.previousEmotion) {
          const prevArt = this.emotionLibrary.get(state.previousEmotion);
          if (prevArt && prevArt.frames.length > 0) {
            const currentFrame = art.frames[0];
            const prevFrame = prevArt.frames[0];
            return this.blendFrames(prevFrame, currentFrame, state.transitionProgress);
          }
        }
        
        // Return current frame - use frame index for animated emotions
        let effectiveFrameIndex = 0;
        if (art.frames.length > 1 && art.loop) {
          effectiveFrameIndex = frameIndex % art.frames.length;
        }
        return art.frames[effectiveFrameIndex];
      })
    );
  }

  /**
   * Get current frame index for an emotion
   */
  private getCurrentFrameIndex(emotion: EmotionType): number {
    const art = this.emotionLibrary.get(emotion);
    if (!art || art.frames.length <= 1 || !art.loop) {
      return 0;
    }
    
    // Return current frame index for looping animations
    return this.frameIndexSubject.value;
  }

  /**
   * Blend two ASCII frames during transition
   */
  private blendFrames(frame1: string, frame2: string, progress: number): string {
    // Simple blending: show frame1 when progress < 0.5, frame2 when progress >= 0.5
    // For more sophisticated blending, we could implement character-by-character transitions
    return progress < 0.5 ? frame1 : frame2;
  }

  /**
   * Start animation for the current emotion
   */
  startAnimation(): void {
    this.stopAnimation();
    
    const currentEmotion = this.currentEmotionSubject.value;
    const art = this.emotionLibrary.get(currentEmotion);
    
    if (!art || art.frames.length <= 1 || !art.loop) {
      this.frameIndexSubject.next(0);
      this.animationRunningSubject.next(false);
      return;
    }

    this.currentFrameIndex = 0;
    this.frameIndexSubject.next(0);
    
    this.activeAnimation = interval(art.frameRate).subscribe(() => {
      this.currentFrameIndex = (this.currentFrameIndex + 1) % art.frames.length;
      this.frameIndexSubject.next(this.currentFrameIndex);
    });
    this.animationRunningSubject.next(true);
  }

  /**
   * Stop current animation
   */
  stopAnimation(): void {
    if (this.activeAnimation) {
      this.activeAnimation.unsubscribe();
      this.activeAnimation = null;
    }
    this.frameIndexSubject.next(0);
    this.currentFrameIndex = 0;
    this.animationRunningSubject.next(false);
  }

  /**
   * Get thinking indicator (spinner) frames
   */
  getThinkingIndicators(): string[] {
    return [
      '⠋ Thinking',
      '⠙ Thinking',
      '⠹ Thinking',
      '⠸ Thinking',
      '⠼ Thinking',
      '⠴ Thinking',
      '⠦ Thinking',
      '⠧ Thinking',
      '⠇ Thinking',
      '⠏ Thinking'
    ];
  }

  /**
   * Get particle effect for message send
   */
  getSendParticles(): string[] {
    return [
      '✨ Sending...',
      '✨✨ Sending...',
      '✨✨✨ Sending...',
      '✨✨✨✨ Sent!'
    ];
  }

  /**
   * Get particle effect for message receive
   */
  getReceiveParticles(): string[] {
    return [
      '📥 Receiving...',
      '📥📥 Receiving...',
      '📥📥📥 Receiving...',
      '📥📥📥📥 Received!'
    ];
  }

  /**
   * Get blinking cursor animation frames
   */
  getCursorFrames(): string[] {
    return [
      '█',
      '▓',
      '▒',
      '░',
      '▒',
      '▓'
    ];
  }

  /**
   * Clean up resources
   */
  ngOnDestroy(): void {
    this.stopAnimation();
    if (this.transitionInterval) {
      this.transitionInterval.unsubscribe();
    }
  }
}