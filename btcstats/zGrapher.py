import sys, pygame
from pygame.locals import *



WHITE = (255,255,255)
GRAY = (136,136,136)
DARKGRAY = (70,70,70)
BLACK = (0,0,0)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)
YELLOW = (255,255,0)
CYAN = (0,255,255)
MAGENTA = (255,0,255)

def random_color():
	return (randint(0,255), randint(0,255), randint(0,255))

def z_text_draw(surface, text, dim, pos, font=None, color=WHITE):
	font = pygame.font.Font(font, int(dim))
	image = font.render(text, 1, color)
	surface.blit(image,pos)


TITLE = "zGrapher"
SCREENSIZE = (SCREENX, SCREENY) = (800, 800)
FPS = 20
BACKGROUND = BLACK


class zGraph:
	def __init__(self, Xdata, Ydata, adjustable, style=0):
		minX, maxX, labelX = Xdata
		minY, maxY, labelY = Ydata
		self.style = style # 0: scatterplot, 1: impulseplot
		self.steps = 14
		self.minX = minX
		self.maxX = maxX
		self.stepX = (self.maxX-self.minX)/float(self.steps)
		self.labelX = labelX
		self.minY = minY
		self.maxY = maxY
		self.stepY = (self.maxY-self.minY)/float(self.steps)
		self.labelY = labelY
		self.data = {}
		self.adjustable = adjustable
		self.surface = pygame.Surface((SCREENX, SCREENY))
		self.surface.fill(BACKGROUND)
		self.surface_created = False

	def insert_data(self, newdata, labelX, labelY):
		self.data.update(newdata)
		self.labelX = labelX
		self.labelY = labelY
		self.surface_created = False

	def adjust_axes(self):
		if self.adjustable:
			self.minX = min(self.data.keys())
			self.maxX = max(self.data.keys())
			self.stepX = (self.maxX-self.minX)/float(self.steps)
			self.minY = min(0.0, min(self.data.values()))
			self.maxY = max(0.0, max(self.data.values()))
			self.stepY = (self.maxY-self.minY)/float(self.steps)
		self.surface_created = False

	def graph_to_surface_coords(self, graphData):
		graphX, graphY = graphData
		marginX = SCREENX/16
		marginY = SCREENY/16
		surfaceX = int(round(marginX + (graphX - self.minX)/float(self.maxX-self.minX)*(SCREENX-2*marginX)))
		surfaceY = SCREENY - int(round(marginY + (graphY - self.minY)/float(self.maxY-self.minY)*(SCREENY-2*marginY)))
		return (surfaceX, surfaceY)

	def surface_to_graph_coords(self, surfaceData):
		surfaceX, surfaceY = surfaceData
		marginX = SCREENX/16
		marginY = SCREENY/16
		graphX = self.minX + (surfaceX - marginX)/float(SCREENX-2*marginX)*(self.maxX-self.minX)
		graphY = self.minY + ((SCREENY - surfaceY) - marginY)/float(SCREENY-2*marginY)*(self.maxY-self.minY)
		return (graphX, graphY)

	def draw_axes(self):
		marginX = SCREENX/16
		marginY = SCREENY/16

		#X axis
		Xaxis_height = self.graph_to_surface_coords((0, 0))[1]
		pygame.draw.line(self.surface, WHITE, (marginX, Xaxis_height), (SCREENX-marginX, Xaxis_height), 1)
		for i in range(0, self.steps+1):
			pygame.draw.line(self.surface, WHITE, ((i+1)*marginX, SCREENY-marginY+5), ((i+1)*marginX, SCREENY-marginY-5), 1)
			z_text_draw(self.surface, "%.2f"%(self.minX+i*self.stepX), 15, ((i+1)*marginX-5, SCREENY-marginY+10), None, WHITE)
		z_text_draw(self.surface, self.labelX, (marginX+marginY)/4, (SCREENX-marginX*2, SCREENY-marginY/2), None, WHITE)

		#Y axis
		pygame.draw.line(self.surface, WHITE, (marginX, SCREENY-marginY), (marginX, marginY), 1)
		for i in range(0, self.steps+1):
			pygame.draw.line(self.surface, WHITE, (marginX-5, SCREENY-(i+1)*marginY), (marginX+5, SCREENY-(i+1)*marginY), 1)
			z_text_draw(self.surface, "%.3f"%(self.minY+i*self.stepY), 15, (10, SCREENY-(i+1)*marginY-3), None, WHITE)
		z_text_draw(self.surface, self.labelY, (marginX+marginY)/4, (marginX/2, marginY/2), None, WHITE)

	def draw_mouse(self, dest_surface):
		mX, mY = pygame.mouse.get_pos()
		pygame.draw.line(dest_surface, DARKGRAY, (0, mY), (SCREENX, mY), 1)
		pygame.draw.line(dest_surface, DARKGRAY, (mX, 0), (mX, SCREENY), 1)
		gX, gY = self.surface_to_graph_coords((mX, mY))
		z_text_draw(dest_surface, "(%.2f, %.3f)"%(gX, gY), 15, (mX+2, mY-10), None, GRAY)

	def draw_data(self):
		for datum in self.data:
			if self.style == 0:
				pos = self.graph_to_surface_coords((datum, self.data[datum]))
				pygame.draw.circle(self.surface, RED, pos, 2, 0)
				#self.surface.set_at(self.graph_to_surface_coords((datum, self.data[datum])), RED)
			elif self.style == 1:
				start = self.graph_to_surface_coords((datum, 0))
				end = self.graph_to_surface_coords((datum, self.data[datum]))
				pygame.draw.line(self.surface, RED, start, end, 2)

	def create_surface(self):
		self.surface.fill(BACKGROUND)
		self.adjust_axes()
		self.draw_axes()
		self.draw_data()
		self.surface_created = True

	def save_plot(self, filename):
		if not self.surface_created:
			self.create_surface()
		pygame.image.save(self.surface, filename)
		print("\nPlot saved to {}\n".format(filename))

	def draw(self, dest_surface):
		if not self.surface_created:
			self.create_surface()
		dest_surface.blit(self.surface, (0,0), None, 0)
		self.draw_mouse(dest_surface)

	def update(self, e): #zooming and panning, not really needed, will implement in the future (aka never)
		return
		if self.adjustable:
			if e.type == MOUSEBUTTONDOWN:
				if e.button == 4:
					pass
				elif e.button == 5:
					pass



def load_data_from_file(filepath):
	data = {}
	labelX = ""
	labelY = ""
	with open(filepath, 'r') as f:
		labelX = f.readline()[:-1]
		labelY = f.readline()[:-1]
		for line in f:
			data.update({float(line[:line.index(' ')]) : float(line[line.index(' ')+1:])})
	#print data
	return data, labelX, labelY



def plot_data(data, labelX, labelY, plotfile, style=0, live=False):
	pygame.init()
	Graph = zGraph((0,100,"x"), (0,100,"y"), True, style)
	Graph.insert_data(data, labelX, labelY)
	Graph.save_plot(plotfile)

	if live:
		screen = pygame.display.set_mode(SCREENSIZE)
		pygame.display.set_caption(TITLE)
		pygame.mouse.set_visible(False)
		clock = pygame.time.Clock()
		RUN = True
		while RUN:
			clock.tick(FPS)

			for event in pygame.event.get():
				if event.type == QUIT:
					RUN = False
				elif event.type == KEYDOWN:
					if event.key == K_ESCAPE:
						RUN = False

				Graph.update(event)

			screen.fill(BLACK)
			Graph.draw(screen)
			z_text_draw(screen, "%.1f"%(clock.get_fps()), 15, (SCREENX-30,10), None, WHITE)
			pygame.display.flip()



if __name__ == '__main__':
	plotfile = sys.argv[1][:-4]+".bmp"
	data, labelX, labelY = load_data_from_file(sys.argv[1])
	plot_data(data, labelX, labelY, plotfile, 0, True)
