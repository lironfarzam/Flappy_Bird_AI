import pygame
import neat
import time
import random
import os

# constants
WIN_WIDTH = 500
WIN_HEIGHT = 800


# bird images 2x
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png"))) ]

# full size bird images
# BIRD_IMGS = [pygame.image.load(os.path.join("imgs", "d1.png")),
#              pygame.image.load(os.path.join("imgs", "d2.png")),
#              pygame.image.load(os.path.join("imgs", "d3.png")) ]

# # bird images 0.5x
# BIRD_IMGS = [pygame.transform.scale(pygame.image.load(os.path.join("imgs", "d1.png")), (75, 75)),
#              pygame.transform.scale(pygame.image.load(os.path.join("imgs", "d2.png")), (75, 75)),
#              pygame.transform.scale(pygame.image.load(os.path.join("imgs", "d3.png")), (75, 75)) ]


PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
# PIPE_IMG = pygame.image.load(os.path.join("imgs", "i2.png"))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))
pygame.font.init() # initialize the font
STAT_FONT = pygame.font.SysFont("comicsans", 50)

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25 # how much the bird will tilt
    ROT_VEL = 20 # how much we will rotate on each frame
    ANIMATION_TIME = 5 # how long each bird animation will last

    def __init__(self, x, y):
        # x and y are the starting position of the bird
        self.x = x
        self.y = y
        self.tilt = 0 # how much the image is tilted
        self.tick_count = 0 # physics of the bird
        self.vel = 0 # velocity
        self.height = self.y # height of the bird
        self.img_count = 0 # which image of the bird we are showing
        self.img = self.IMGS[0] # the image of the bird

    def jump(self):
        self.vel = -10.5 # negative velocity because top left corner is 0,0
        self.tick_count = 0 # keep track of when we last jumped
        self.height = self.y # where the bird jumped from

    def move(self):
        self.tick_count += 1 # how many times we moved since last jump
        d = self.vel*self.tick_count + 1.5*self.tick_count**2 # how many pixels we are moving up or down

        if d >= 16: # if we are moving down more than 16 pixels
            d = 16 # we don't want to move down more than 16 pixels

        if d < 0: # if we are moving up
            d -= 2 # move up a little bit more

        self.y = self.y + d # move the bird up or down

        if d < 0 or self.y < self.height + 50: # if we are moving up or we are above the original height
            if self.tilt < self.MAX_ROTATION: # if we are not tilted too much
                self.tilt = self.MAX_ROTATION # tilt the bird
        else: # if we are moving down
            if self.tilt > -90: # if we are not tilted too much
                self.tilt -= self.ROT_VEL # tilt the bird

    def draw(self, win):
        self.img_count += 1 # how many times we showed the same image

        # which image of the bird we are showing
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # if we are moving down, we don't want to animate the bird
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        # rotate the image around the center
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x,self.y)).center) # rotate around the center
        win.blit(rotated_image, new_rect.topleft) # draw the rotated image

    def get_mask(self):
        return pygame.mask.from_surface(self.img)
    
class Pipe:
    GAP = 200 # space between the pipes
    VEL = 5 # how fast the pipes are moving

    def __init__(self, x):
        self.x = x # x position of the pipe
        self.height = 0 # height of the pipe
        self.top = 0 # where the top of the pipe is drawn
        self.bottom = 0 # where the bottom of the pipe is drawn
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True) # flip the pipe image
        self.PIPE_BOTTOM = PIPE_IMG # pipe image
        self.passed = False # if the bird passed the pipe
        self.set_height() # set the height of the pipe

    def set_height(self):
        self.height = random.randrange(50, 450) # random height of the pipe
        self.top = self.height - self.PIPE_TOP.get_height() # top of the pipe
        self.bottom = self.height + self.GAP # bottom of the pipe

    def move(self):
        self.x -= self.VEL # move the pipe

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top)) # draw the top pipe
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom)) # draw the bottom pipe

    def collide(self, bird):
        # get the masks of the bird and the pipes
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP) # mask of the top pipe
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM) # mask of the bottom pipe

        # offset is how far away the masks are from each other
        top_offset = (self.x - bird.x, self.top - round(bird.y)) # offset of the top pipe
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y)) # offset of the bottom pipe

        # point of collision
        b_point = bird_mask.overlap(bottom_mask, bottom_offset) # point of collision with the bottom pipe
        t_point = bird_mask.overlap(top_mask, top_offset) # point of collision with the top pipe

        if t_point or b_point: # if we collided with the top or bottom pipe
            return True # we collided

        return False # we didn't collide
    
class Base:
    VEL = 5 # how fast the base is moving
    WIDTH = BASE_IMG.get_width() # width of the base
    IMG = BASE_IMG # image of the base

    def __init__(self, y):
        self.y = y # y position of the base
        self.x1 = 0 # first image of the base
        self.x2 = self.WIDTH # second image of the base

    def move(self):
        self.x1 -= self.VEL # move the first image of the base
        self.x2 -= self.VEL # move the second image of the base

        # if the first image of the base is off the screen
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH # move the first image to the right of the second image

        # if the second image of the base is off the screen
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH # move the second image to the right of the first image

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y)) # draw the first image of the base
        win.blit(self.IMG, (self.x2, self.y)) # draw the second image of the base

# --------------------------------------------------------------- #
def draw_window1(win, bird, pipes, base, score):
    win.blit(BG_IMG, (0,0)) # draw the background
    
    for pipe in pipes:# draw the pipes
        pipe.draw(win)


    text = STAT_FONT.render("Score: " + str(score), 1, (255,255,255)) # draw the score
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10)) # draw the score
    
    base.draw(win) # draw the base

    bird.draw(win) # draw the bird
    pygame.display.update() # update the display

def main1():
    # Initialize Pygame
    pygame.init()

    # Create the game window and clock
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption("Flappy Bird!")
    clock = pygame.time.Clock()

    # Create game elements
    bird = Bird(230, 350)
    base = Base(730)
    pipes = [Pipe(600)]
    score = 0

    # Game loop
    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.jump()

        bird.move()
        base.move()

        # Generate pipes and handle collisions
        for pipe in pipes:
            pipe.move()
            if pipe.collide(bird):
                # Game over logic
                run = False
                break
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                pipes.remove(pipe)
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                score += 1
                pipes.append(Pipe(WIN_WIDTH))

        # Check for bird hitting the ground or going above the screen
        if bird.y + bird.img.get_height() >= 730:
            # Game over logic
            run = False

        # Draw the game window
        draw_window1(win, bird, pipes, base, score)

    # Game over message
    game_over_text = STAT_FONT.render("Game Over", 1, (255, 0, 0))
    win.blit(game_over_text, (WIN_WIDTH // 2 - game_over_text.get_width() // 2, WIN_HEIGHT // 2 - game_over_text.get_height() // 2))
    pygame.display.update()

    # Delay before quitting the game
    pygame.time.delay(2000)
    print("\033[92m" + "[INFO] Game Over" + "\033[0m")
    print("\033[92m" + "[INFO] Score: " + str(score) + "\033[0m")
    pygame.quit()
# --------------------------------------------------------------- #

def draw_window(win, birds, pipes, base, score):
    win.blit(BG_IMG, (0,0)) # draw the background
    
    for pipe in pipes:# draw the pipes
        pipe.draw(win)


    text = STAT_FONT.render("Score: " + str(score), 1, (255,255,255)) # draw the score
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10)) # draw the score
    
    base.draw(win) # draw the base

    for bird in birds:
        bird.draw(win) # draw the bird
    pygame.display.update() # update the display

def main(genomes, config):
    print("\033[92m" + "[INFO] Starting Flappy Bird..." + "\033[0m")

    nets = []
    ge = []

    birds = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230,350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0

    run = True
    while run:
        clock.tick(30) # 30 fps
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        for i, bird in enumerate(birds):
            bird.move()
            ge[i].fitness += 0.1

            output = nets[i].activate((bird.y,abs(bird.y - pipes[pipe_ind].height),abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5:
                bird.jump()
        
        base.move()
        add_pipe = False
        rem = []
        for pipe in pipes:
            for i,bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[i].fitness -= 1
                    birds.pop(i)
                    nets.pop(i)
                    ge.pop(i)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0: # if the pipe is off the screen 
                rem.append(pipe) # remove the pipe

            pipe.move()

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        for i, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(i)
                nets.pop(i)
                ge.pop(i)

        # bird.move()
        draw_window(win, birds, pipes, base, score)




def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path) # load the config file
    
    p = neat.Population(config) # create the population

    p.add_reporter(neat.StdOutReporter(True)) # show the statistics
    p.add_reporter(neat.StatisticsReporter())

    winner = p.run(main, 50) # run the main function 50 times


  
  
if __name__ == "__main__":
    local_dir = os.path.dirname(__file__) # get the current directory
    config_path = os.path.join(local_dir, "config.txt") # get the path of the config file
    run(config_path) # run the main function 
    # i = 1
    # while True:
    #     print("\033[92m" + "[INFO] Starting Flappy Bird " + str(i) + "..." + "\033[0m")
    #     main1()
    #     i += 1
        


