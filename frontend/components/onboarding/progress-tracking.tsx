'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Trophy,
  Target,
  CheckCircle,
  Circle,
  Lock,
  Unlock,
  Star,
  TrendingUp,
  Award,
  Zap,
  Users,
  Shield,
  BarChart3,
  MessageSquare,
  Settings,
  BookOpen,
  Video,
  FileText,
  Gift,
  ChevronRight
} from 'lucide-react'

interface OnboardingTask {
  id: string
  category: string
  title: string
  description: string
  points: number
  completed: boolean
  required: boolean
  dependsOn?: string[]
  action?: {
    label: string
    onClick: () => void
  }
}

interface Achievement {
  id: string
  title: string
  description: string
  icon: React.ElementType
  tier: 'bronze' | 'silver' | 'gold' | 'platinum'
  progress: number
  maxProgress: number
  unlocked: boolean
  unlockedAt?: Date
  reward?: string
}

interface OnboardingCategory {
  id: string
  name: string
  icon: React.ElementType
  description: string
  tasks: OnboardingTask[]
}

const ONBOARDING_CATEGORIES: OnboardingCategory[] = [
  {
    id: 'getting-started',
    name: 'Getting Started',
    icon: Rocket,
    description: 'Complete the basics to get up and running',
    tasks: [
      {
        id: 'complete-tour',
        category: 'getting-started',
        title: 'Complete the welcome tour',
        description: 'Get familiar with the SentinelOps interface',
        points: 10,
        completed: false,
        required: true
      },
      {
        id: 'first-login',
        category: 'getting-started',
        title: 'Set up your profile',
        description: 'Add your name and preferences',
        points: 5,
        completed: false,
        required: true
      },
      {
        id: 'enable-notifications',
        category: 'getting-started',
        title: 'Enable notifications',
        description: 'Stay informed about security events',
        points: 5,
        completed: false,
        required: false
      }
    ]
  },
  {
    id: 'security-basics',
    name: 'Security Basics',
    icon: Shield,
    description: 'Learn core security concepts',
    tasks: [
      {
        id: 'view-incident',
        category: 'security-basics',
        title: 'View your first incident',
        description: 'Open and review an incident details page',
        points: 10,
        completed: false,
        required: true,
        dependsOn: ['complete-tour']
      },
      {
        id: 'acknowledge-incident',
        category: 'security-basics',
        title: 'Acknowledge an incident',
        description: 'Mark an incident as acknowledged',
        points: 15,
        completed: false,
        required: true,
        dependsOn: ['view-incident']
      },
      {
        id: 'run-scenario',
        category: 'security-basics',
        title: 'Complete a practice scenario',
        description: 'Run through a simulated security incident',
        points: 20,
        completed: false,
        required: false
      }
    ]
  },
  {
    id: 'ai-features',
    name: 'AI Features',
    icon: Sparkles,
    description: 'Explore AI-powered capabilities',
    tasks: [
      {
        id: 'chat-interaction',
        category: 'ai-features',
        title: 'Ask the AI assistant a question',
        description: 'Use natural language to get insights',
        points: 15,
        completed: false,
        required: false
      },
      {
        id: 'view-ai-analysis',
        category: 'ai-features',
        title: 'Review AI analysis',
        description: 'See how AI agents analyze incidents',
        points: 10,
        completed: false,
        required: false
      },
      {
        id: 'approve-remediation',
        category: 'ai-features',
        title: 'Approve an AI remediation',
        description: 'Review and approve an AI-suggested fix',
        points: 20,
        completed: false,
        required: false,
        dependsOn: ['acknowledge-incident']
      }
    ]
  },
  {
    id: 'customization',
    name: 'Customization',
    icon: Settings,
    description: 'Personalize your experience',
    tasks: [
      {
        id: 'customize-dashboard',
        category: 'customization',
        title: 'Customize your dashboard',
        description: 'Add or rearrange dashboard widgets',
        points: 10,
        completed: false,
        required: false
      },
      {
        id: 'create-filter',
        category: 'customization',
        title: 'Create a saved filter',
        description: 'Save a custom incident filter',
        points: 10,
        completed: false,
        required: false
      },
      {
        id: 'set-preferences',
        category: 'customization',
        title: 'Configure preferences',
        description: 'Set your notification and display preferences',
        points: 5,
        completed: false,
        required: false
      }
    ]
  }
]

const ACHIEVEMENTS: Achievement[] = [
  {
    id: 'first-steps',
    title: 'First Steps',
    description: 'Complete the welcome tour',
    icon: Trophy,
    tier: 'bronze',
    progress: 0,
    maxProgress: 1,
    unlocked: false
  },
  {
    id: 'security-novice',
    title: 'Security Novice',
    description: 'Handle your first 5 incidents',
    icon: Shield,
    tier: 'bronze',
    progress: 0,
    maxProgress: 5,
    unlocked: false
  },
  {
    id: 'ai-explorer',
    title: 'AI Explorer',
    description: 'Use all AI features',
    icon: Sparkles,
    tier: 'silver',
    progress: 0,
    maxProgress: 3,
    unlocked: false
  },
  {
    id: 'power-user',
    title: 'Power User',
    description: 'Complete all onboarding tasks',
    icon: Zap,
    tier: 'gold',
    progress: 0,
    maxProgress: 15,
    unlocked: false,
    reward: 'Unlock advanced features'
  },
  {
    id: 'security-expert',
    title: 'Security Expert',
    description: 'Complete all practice scenarios',
    icon: Award,
    tier: 'platinum',
    progress: 0,
    maxProgress: 3,
    unlocked: false,
    reward: 'Expert badge on profile'
  }
]

interface ProgressTrackingProps {
  onTaskComplete?: (taskId: string) => void
  onAchievementUnlock?: (achievementId: string) => void
}

export function ProgressTracking({ 
  onTaskComplete,
  onAchievementUnlock 
}: ProgressTrackingProps) {
  const [tasks, setTasks] = useState<OnboardingTask[]>([])
  const [achievements, setAchievements] = useState<Achievement[]>(ACHIEVEMENTS)
  const [showReward, setShowReward] = useState<Achievement | null>(null)

  // Initialize tasks from all categories
  useEffect(() => {
    const allTasks = ONBOARDING_CATEGORIES.flatMap(cat => cat.tasks)
    
    // Load saved progress
    const savedProgress = localStorage.getItem('onboardingProgress')
    if (savedProgress) {
      const completed = JSON.parse(savedProgress)
      const tasksWithProgress = allTasks.map(task => ({
        ...task,
        completed: completed.includes(task.id)
      }))
      setTasks(tasksWithProgress)
    } else {
      setTasks(allTasks)
    }
  }, [])

  // Calculate overall progress
  const totalTasks = tasks.length
  const completedTasks = tasks.filter(t => t.completed).length
  const totalPoints = tasks.reduce((sum, t) => sum + t.points, 0)
  const earnedPoints = tasks.filter(t => t.completed).reduce((sum, t) => sum + t.points, 0)
  const overallProgress = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0

  // Check if task can be started
  const canStartTask = (task: OnboardingTask) => {
    if (!task.dependsOn || task.dependsOn.length === 0) return true
    return task.dependsOn.every(depId => tasks.find(t => t.id === depId)?.completed)
  }

  // Complete a task
  const completeTask = (taskId: string) => {
    const updatedTasks = tasks.map(task => 
      task.id === taskId ? { ...task, completed: true } : task
    )
    setTasks(updatedTasks)

    // Save progress
    const completedIds = updatedTasks.filter(t => t.completed).map(t => t.id)
    localStorage.setItem('onboardingProgress', JSON.stringify(completedIds))

    // Check for achievement unlocks
    checkAchievements(updatedTasks)

    if (onTaskComplete) {
      onTaskComplete(taskId)
    }
  }

  // Check and update achievements
  const checkAchievements = (currentTasks: OnboardingTask[]) => {
    const updatedAchievements = [...achievements]
    let newUnlock: Achievement | null = null

    // First Steps - Complete welcome tour
    const firstSteps = updatedAchievements.find(a => a.id === 'first-steps')
    if (firstSteps && !firstSteps.unlocked && currentTasks.find(t => t.id === 'complete-tour')?.completed) {
      firstSteps.progress = 1
      firstSteps.unlocked = true
      firstSteps.unlockedAt = new Date()
      newUnlock = firstSteps
    }

    // Power User - Complete all tasks
    const powerUser = updatedAchievements.find(a => a.id === 'power-user')
    if (powerUser) {
      powerUser.progress = currentTasks.filter(t => t.completed).length
      if (!powerUser.unlocked && powerUser.progress >= powerUser.maxProgress) {
        powerUser.unlocked = true
        powerUser.unlockedAt = new Date()
        newUnlock = powerUser
      }
    }

    setAchievements(updatedAchievements)

    if (newUnlock) {
      setShowReward(newUnlock)
      if (onAchievementUnlock) {
        onAchievementUnlock(newUnlock.id)
      }
    }
  }

  const getTierColor = (tier: Achievement['tier']) => {
    switch (tier) {
      case 'bronze':
        return 'text-orange-600 bg-orange-50 border-orange-200'
      case 'silver':
        return 'text-gray-600 bg-gray-50 border-gray-200'
      case 'gold':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'platinum':
        return 'text-purple-600 bg-purple-50 border-purple-200'
    }
  }

  return (
    <div className="space-y-6">
      {/* Overall Progress */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold">Your Progress</h2>
            <p className="text-gray-500">
              {completedTasks} of {totalTasks} tasks completed
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-blue-600">
              {earnedPoints}
            </div>
            <p className="text-sm text-gray-500">points earned</p>
          </div>
        </div>
        
        <Progress value={overallProgress} className="h-3 mb-4" />
        
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold">{completedTasks}</div>
            <p className="text-sm text-gray-500">Completed</p>
          </div>
          <div>
            <div className="text-2xl font-bold">{totalTasks - completedTasks}</div>
            <p className="text-sm text-gray-500">Remaining</p>
          </div>
          <div>
            <div className="text-2xl font-bold">
              {achievements.filter(a => a.unlocked).length}
            </div>
            <p className="text-sm text-gray-500">Achievements</p>
          </div>
          <div>
            <div className="text-2xl font-bold">
              {Math.round(overallProgress)}%
            </div>
            <p className="text-sm text-gray-500">Complete</p>
          </div>
        </div>
      </Card>

      {/* Tasks and Achievements Tabs */}
      <Tabs defaultValue="tasks" className="space-y-4">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="tasks">Tasks</TabsTrigger>
          <TabsTrigger value="achievements">Achievements</TabsTrigger>
        </TabsList>

        <TabsContent value="tasks" className="space-y-4">
          {ONBOARDING_CATEGORIES.map((category) => {
            const Icon = category.icon
            const categoryTasks = tasks.filter(t => t.category === category.id)
            const completedCount = categoryTasks.filter(t => t.completed).length
            const categoryProgress = categoryTasks.length > 0 
              ? (completedCount / categoryTasks.length) * 100 
              : 0

            return (
              <Card key={category.id} className="p-4">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold">{category.name}</h3>
                    <p className="text-sm text-gray-500">{category.description}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">
                      {completedCount}/{categoryTasks.length}
                    </div>
                    <Progress value={categoryProgress} className="w-20 h-2" />
                  </div>
                </div>

                <div className="space-y-2">
                  {categoryTasks.map((task) => {
                    const isLocked = !canStartTask(task)
                    
                    return (
                      <div
                        key={task.id}
                        className={`flex items-center justify-between p-3 rounded-lg border ${
                          task.completed 
                            ? 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800'
                            : isLocked
                            ? 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-800 opacity-50'
                            : 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          {task.completed ? (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          ) : isLocked ? (
                            <Lock className="h-5 w-5 text-gray-400" />
                          ) : (
                            <Circle className="h-5 w-5 text-gray-400" />
                          )}
                          <div>
                            <div className="font-medium flex items-center gap-2">
                              {task.title}
                              {task.required && (
                                <Badge variant="outline" className="text-xs">
                                  Required
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-gray-500">{task.description}</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-3">
                          <Badge variant="secondary">
                            {task.points} pts
                          </Badge>
                          {!task.completed && !isLocked && task.action && (
                            <Button
                              size="sm"
                              onClick={() => {
                                task.action?.onClick()
                                // Simulate completion for demo
                                setTimeout(() => completeTask(task.id), 2000)
                              }}
                            >
                              {task.action.label}
                              <ChevronRight className="h-4 w-4 ml-1" />
                            </Button>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </Card>
            )
          })}
        </TabsContent>

        <TabsContent value="achievements" className="space-y-4">
          <div className="grid gap-4">
            {achievements.map((achievement) => {
              const Icon = achievement.icon
              const progressPercent = (achievement.progress / achievement.maxProgress) * 100
              
              return (
                <Card
                  key={achievement.id}
                  className={`p-4 ${
                    achievement.unlocked 
                      ? 'bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20' 
                      : ''
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <div className={`p-3 rounded-lg border ${getTierColor(achievement.tier)}`}>
                      <Icon className="h-6 w-6" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold">{achievement.title}</h3>
                        <Badge 
                          variant={achievement.unlocked ? 'default' : 'outline'}
                          className="text-xs"
                        >
                          {achievement.tier}
                        </Badge>
                        {achievement.unlocked && (
                          <Badge variant="secondary" className="text-xs">
                            <Star className="h-3 w-3 mr-1" />
                            Unlocked
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 mb-2">
                        {achievement.description}
                      </p>
                      
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span>Progress</span>
                          <span>{achievement.progress}/{achievement.maxProgress}</span>
                        </div>
                        <Progress value={progressPercent} className="h-2" />
                      </div>

                      {achievement.reward && (
                        <div className="mt-3 flex items-center gap-2 text-sm">
                          <Gift className="h-4 w-4 text-purple-600" />
                          <span className="text-purple-600 font-medium">
                            Reward: {achievement.reward}
                          </span>
                        </div>
                      )}

                      {achievement.unlockedAt && (
                        <p className="text-xs text-gray-400 mt-2">
                          Unlocked {achievement.unlockedAt.toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>
                </Card>
              )
            })}
          </div>
        </TabsContent>
      </Tabs>

      {/* Achievement Unlock Modal */}
      {showReward && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <Card className="max-w-md p-8 text-center">
            <div className="mb-6">
              <div className={`inline-flex p-4 rounded-full ${getTierColor(showReward.tier)}`}>
                <Trophy className="h-12 w-12" />
              </div>
            </div>
            
            <h2 className="text-2xl font-bold mb-2">Achievement Unlocked!</h2>
            <h3 className="text-xl mb-4">{showReward.title}</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {showReward.description}
            </p>
            
            {showReward.reward && (
              <div className="p-4 bg-purple-50 dark:bg-purple-950 rounded-lg mb-6">
                <p className="text-purple-600 dark:text-purple-400 font-medium">
                  🎁 {showReward.reward}
                </p>
              </div>
            )}
            
            <Button onClick={() => setShowReward(null)}>
              Awesome!
            </Button>
          </Card>
        </div>
      )}
    </div>
  )
}