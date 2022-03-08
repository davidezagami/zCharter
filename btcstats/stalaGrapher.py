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
	surface.blit(image, pos)

def z_font_draw(surface, text, pos, font, color=WHITE):
	image = font.render(text, 1, color)
	surface.blit(image, pos)


TITLE = "stalaGrapher"
SCREENSIZE = (SCREENX, SCREENY) = (800, 800)
FPS = 20
BACKGROUND = BLACK



class stalaGraph:
	def __init__(self, Xaxis, Yaxis, resolution, title, subtitle, datanames=None):
		minX, maxX, labelX = Xaxis
		minY, maxY, labelY = Yaxis
		self.minX = minX
		self.maxX = maxX
		self.labelX = labelX
		self.minY = minY
		self.maxY = maxY
		self.labelY = labelY
		self.resolution = resolution
		self.data = []
		self.title = title
		self.subtitle = subtitle
		self.surface = pygame.Surface((SCREENX, SCREENY))
		self.surface.fill(BACKGROUND)
		self.surface_created = False
		self.space_between_datums = 90
		self.marginX = SCREENX/16
		self.marginY = SCREENY/16
		self.datum_max_width = 60
		self.titlesize = 40
		self.subtitlesize = 20
		self.y_unit = 25/self.resolution
		self.max_from_dataset = 0
		self.datanames = datanames
		if not datanames:
			self.datanames = [str(i) for i in range(self.maxX)]

	def insert_data(self, newdata):
		self.data += newdata
		self.y_unit = 20.0/len(newdata[0]) * 25.0/self.resolution
		self.max_from_dataset = max(( max(data_each_day.values()) for data_each_day in self.data ))
		self.surface_created = False

	def graph_to_surface_coords(self, graphData):
		graphX, graphY = graphData
		surfaceX = int(round(self.marginX + (graphX - self.minX)/float(self.maxX-self.minX)*(SCREENX-2*self.marginX)))
		surfaceY = SCREENY - int(round(self.marginY + (graphY - self.minY)/float(self.maxY-self.minY)*(SCREENY-2*self.marginY)))
		return (surfaceX, surfaceY)

	def surface_to_graph_coords(self, surfaceData):
		surfaceX, surfaceY = surfaceData
		graphX = self.minX + (surfaceX - self.marginX)/float(SCREENX-2*self.marginX)*(self.maxX-self.minX)
		graphY = self.minY + ((SCREENY - surfaceY) - self.marginY)/float(SCREENY-2*self.marginY)*(self.maxY-self.minY)
		return (graphX, graphY)

	def datum_x_offset(self, index):
		return self.marginX + self.space_between_datums*(index+1)

	def draw_axes(self):
		#X axis
		start_point = (self.marginX, SCREENY/2)
		end_point = (SCREENX-self.marginX, SCREENY/2)
		pygame.draw.line(self.surface, WHITE, start_point, end_point, 1)
		z_text_draw(self.surface, self.labelX, (self.marginX+self.marginY)/4, (SCREENX-self.marginX+5, SCREENY/2-5), None, WHITE)

		#Y axis
		start_point = (self.marginX, SCREENY-self.marginY)
		end_point = (self.marginX, self.marginY)
		pygame.draw.line(self.surface, WHITE, start_point, end_point, 1)
		z_text_draw(self.surface, self.labelY, (self.marginX+self.marginY)/4, (self.marginX/2, self.marginY/2), None, WHITE)

		upperbound_pos_start = (self.marginX-10, SCREENY/2 - self.y_unit*self.maxY)
		upperbound_pos_end = (self.marginX+10, SCREENY/2 - self.y_unit*self.maxY)
		pygame.draw.line(self.surface, WHITE, upperbound_pos_start, upperbound_pos_end, 1)
		z_text_draw(self.surface, "{:+.0f}%".format(self.maxY*100), 20, upperbound_pos_end, None, WHITE)
		lowerbound_pos_start = (self.marginX-10, SCREENY/2 - self.y_unit*self.minY)
		lowerbound_pos_end = (self.marginX+10, SCREENY/2 - self.y_unit*self.minY)
		pygame.draw.line(self.surface, WHITE, lowerbound_pos_start, lowerbound_pos_end, 1)
		z_text_draw(self.surface, "{:+.0f}%".format(self.minY*100), 20, lowerbound_pos_end, None, WHITE)
		z_text_draw(self.surface, "+0%", 20, (self.marginX+5, SCREENY/2), None, WHITE)


	def draw_mouse(self, dest_surface):
		mX, mY = pygame.mouse.get_pos()
		pygame.draw.line(dest_surface, DARKGRAY, (0, mY), (SCREENX, mY), 1)
		pygame.draw.line(dest_surface, DARKGRAY, (mX, 0), (mX, SCREENY), 1)
		#gX, gY = self.surface_to_graph_coords((mX, mY))
		#z_text_draw(dest_surface, "(%.2f, %.3f)"%(gX, gY), 15, (mX+2, mY-10), None, GRAY)

	def draw_data(self):
		for i in range(self.maxX):
			x_data_text_pos = (self.datum_x_offset(i)-self.marginX/2, SCREENY-self.marginY*2)
			z_text_draw(self.surface, self.datanames[i], 40, x_data_text_pos, None, WHITE)

		i=0
		while i < len(self.data):
			minimum_fucking_height = int(self.y_unit*(self.minY-self.resolution))
			for interval in self.data[i]:
				datum_rect = pygame.Rect(0, 0, 0, 0)
				datum_rect.height = int(self.y_unit*self.resolution)
				datum_rect.width = int(self.datum_max_width * self.data[i][interval]/self.max_from_dataset)
				datum_rect.centerx = self.datum_x_offset(i)
				datum_y_offset = max(int(self.y_unit*interval[0]), minimum_fucking_height)
				datum_rect.bottom = SCREENY/2 - datum_y_offset
				pygame.draw.rect(self.surface, WHITE, datum_rect)
			i+=1

	def draw_titles(self):
		title_x_pos = SCREENX/2 - self.titlesize*4
		title_y_pos = self.marginY/2
		subtitle_x_pos = SCREENX/2 - self.subtitlesize*4
		subtitle_y_pos = self.marginY
		z_text_draw(self.surface, self.title, self.titlesize, (title_x_pos, title_y_pos), None, WHITE)
		z_text_draw(self.surface, self.subtitle, self.subtitlesize, (subtitle_x_pos, subtitle_y_pos), None, WHITE)

	def create_surface(self):
		self.surface.fill(BACKGROUND)
		self.draw_axes()
		self.draw_data()
		self.draw_titles()
		self.surface_created = True

	def save_plot(self, filename):
		if not self.surface_created:
			self.create_surface()
		pygame.image.save(self.surface, filename)
		print("\nPlot saved to {}\n".format(filename))

	def draw(self, dest_surface):
		if not self.surface_created:
			self.create_surface()
		dest_surface.blit(self.surface, (0, 0), None, 0)
		self.draw_mouse(dest_surface)

	def update(self, e): #zooming and panning, not really needed, will implement in the future (aka never)
		return
		if self.adjustable:
			if e.type == MOUSEBUTTONDOWN:
				if e.button == 4:
					pass
				elif e.button == 5:
					pass



def plot_analysis(data, graph_title, graph_subtitle, radius, resolution, plotfile, datanames=None, live=False):
	pygame.init()

	Graph = stalaGraph((0, len(data), "Day"),
					(-radius, radius, "% Change since Mon"),
					resolution, graph_title, graph_subtitle, datanames)
	Graph.insert_data(data)
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

			screen.fill(BACKGROUND)
			Graph.draw(screen)
			z_text_draw(screen, "{:.1f} FPS".format(clock.get_fps()), 15, (SCREENX-60, 10), None, WHITE)
			pygame.display.flip()



if __name__ == '__main__':
	print("No example to show")
