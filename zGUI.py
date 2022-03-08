import pygame
from pygame.locals import *
import os
from random import randint



WHITEST = (255,255,255)
WHITE = (224,224,224)
LIGHTGRAY = (192,192,192)
GRAY = (128,128,128)
DARKGRAY = (64,64,64)
BLACK = (0,0,0)
RED = (255,0,0)
MEDIUMRED = (192,0,0)
DARKRED = (128,0,0)
GREEN = (0,255,0)
MEDIUMGREEN = (0,192,0)
DARKGREEN = (0,128,0)
LIGHTBLUE = (0,0,255)
BLUE = (0,0,224)
MEDIUMBLUE = (0,0,192)
DARKBLUE = (0,0,128)
DARKERBLUE = (0,0,96)
DARKESTBLUE = (0,0,64)
YELLOW = (255,255,0)
MEDIUMYELLOW = (192,192,0)
DARKYELLOW = (128,128,0)
CYAN = (0,255,255)
MAGENTA = (255,0,255)

def random_color():
	return (randint(0,255), randint(0,255), randint(0,255))

def z_text_draw(surface, text, fontsize, pos, font=None, color=WHITE):
	font = pygame.font.Font(font, int(fontsize))
	image = font.render(text, 1, color)
	surface.blit(image,pos)

# works only for horizontal or vertical lines
def draw_alpha_line(dest_surface, color, start_pos, end_pos, width=1):
	sizex = abs(start_pos[0] - end_pos[0])
	sizey = abs(start_pos[1] - end_pos[1])
	if sizex == 0:
		sizex = width
	else:
		sizey = width
	line_surf = pygame.Surface((sizex, sizey), flags=pygame.SRCALPHA)
	line_surf.fill(color)
	dest_surface.blit(line_surf, start_pos)



class zEngine(object):
	def __init__(self, size, title=None):
		super(zEngine, self).__init__()
		self.zID = 0
		self.elements = {0:self} # zID:0 is the engine
		zWindow(self, size, title) # zID:1 is the main window, zElement's constructor automatically adds it to the engine's elements


	def get_new_zID(self, new_element):
		new_zID = max(self.elements.keys()) + 1
		self.elements[new_zID] = new_element
		return new_zID


	def delete_zID(self, zID):
		if isinstance(zID, int):
			print("Deleting zID {:d} - {:s}".format(zID, str(self.elements[zID])))
			del self.elements[zID]


	def get_window(self):
		return self.elements[1]


	def get_widgets(self):
		widget_ids = list(self.elements.keys())
		widget_ids.remove(0)
		widget_ids.remove(1)
		widgets = list(self.elements[zid] for zid in widget_ids)
		panels = list(w for w in widgets if isinstance(w, zPanel))
		others = list(w for w in widgets if not isinstance(w, zPanel))
		return panels, others


	def handle_events(self):
		for event in pygame.event.get():
			if event.type == QUIT:
				return False
			elif event.type == KEYDOWN:
				if event.key == K_ESCAPE:
					return False
			for widget in self.get_widgets()[1]:
				widget.update(event)
		return True


	def handle_draws(self):
		self.get_window().new_frame()
		widgets = self.get_widgets()
		for panel in widgets[0]:
			panel.new_frame()
		for widget in widgets[1]:
			widget.draw()
		for panel in widgets[0]:
			panel.draw()
		pygame.display.flip()



class zElement(object):
	def __init__(self, engine):
		super(zElement, self).__init__()
		self.engine = engine
		self.zID = engine.get_new_zID(self)


	def __lt__(self, other):
		return self.zID < other.zID


	def __le__(self, other):
		return self.zID <= other.zID


	def __eq__(self, other):
		return self.zID == other.zID


	def __ne__(self, other):
		return self.zID != other.zID


	def __gt__(self, other):
		return self.zID > other.zID


	def __ge__(self, other):
		return self.zID >= other.zID



class zWindow(zElement):
	def __init__(self, engine, size, title=None):
		super(zWindow, self).__init__(engine)
		#self.engine = engine
		self.x_size, self.y_size = size
		self.title = title
		if title == None:
			self.title = "zEngine App"

		os.environ['SDL_VIDEO_CENTERED'] = '1'
		pygame.init()
		self.screen = pygame.display.set_mode(size)
		pygame.display.set_caption(self.title)
		self.mode = 0 # 0: no refresh, 1: fill, 2: blit
		self.fillcolor = BLACK
		self.blitsurf = None


	def set_refresh_behaviour(self, mode, filler):
		self.mode = mode
		if mode == 1:
			self.fillcolor = filler
		if mode == 2:
			self.blitsurf = filler.copy()


	def new_frame(self):
		if self.mode == 1:
			self.screen.fill(self.fillcolor)
		if self.mode == 2:
			self.screen.blit(self.blitsurf, (0,0))



class zWidget(zElement):
	def __init__(self, engine, target_surface=None):
		super(zWidget, self).__init__(engine)
		#self.engine = engine
		self.target_surface = target_surface
		if target_surface == None:
			self.target_surface = self.engine.get_window().screen

		self.bg_color = WHITE
		self.fg_color = BLACK
		self.btn_color = BLUE
		self.position = (0,0)
		self.surf_size = (1,1)
		self.surface = pygame.Surface(self.surf_size)
		self.rect = self.surface.get_rect(topleft=self.position)


	def set_pos(self, pos):
		self.position = pos
		self.rect.topleft = self.position


	def get_pos(self):
		return self.position


	def set_target_surface(self, new_target):
		self.target_surface = new_target


	def collidepoint(self, point):
		return self.rect.collidepoint(point)


	def make_surface(self):
		print("make_surface method not implemented for zID:{:d} - {:s}".format(self.zID, str(self)))


	def update(self, event):
		print("zID:{:d} - {:s} received {:s}".format(self.zID, str(self), str(event)))


	def draw(self, dest_surface=None):
		if dest_surface == None:
			dest_surface = self.target_surface
		dest_surface.blit(self.surface, self.position)



class zPanel(zWidget):
	def __init__(self, engine, size):
		super(zPanel, self).__init__(engine)
		self.size = size
		self.surface = pygame.Surface(self.size)
		self.rect = self.surface.get_rect(topleft=self.position)
		self.widgets = []
		self.mode = 0 # 0: no refresh, 1: fill, 2: blit
		self.fillcolor = BLACK
		self.blitsurf = None


	def add_widget(self, new_widget):
		new_widget.set_target_surface(self.surface)
		self.widgets.append(new_widget)


	def set_pos(self, pos):
		self.position = pos
		self.rect.topleft = self.position
		for widget in self.widgets:
			widget.rect.topleft = (self.position[0] + widget.position[0], self.position[1] + widget.position[1])


	def set_target_surface(self, new_target):
		self.target_surface = new_target


	def set_refresh_behaviour(self, mode, filler):
		self.mode = mode
		if mode == 1:
			self.fillcolor = filler
		if mode == 2:
			self.blitsurf = filler.copy()


	def update(self, event):
		pass


	def new_frame(self):
		if self.mode == 1:
			self.surface.fill(self.fillcolor)
		if self.mode == 2:
			self.surface.blit(self.blitsurf, (0,0))



class zImage(zWidget):
	def __init__(self, engine, size, color):
		super(zImage, self).__init__(engine)
		self.size = size
		self.surface = pygame.Surface(self.size)
		self.surface.fill(color)


	def update(self, event):
		pass



class zLabel(zWidget):
	def __init__(self, engine, text, font_size=10, font=None, color=WHITE):
		super(zLabel, self).__init__(engine)
		self.text = text
		self.font_size = font_size
		self.font = font
		self.font_renderer = pygame.font.Font(font, int(font_size))
		self.color = color
		self.surface = self.font_renderer.render(self.text, 1, self.color)


	def set_text(self, newtext):
		self.text = newtext
		self.font_renderer = pygame.font.Font(self.font, int(self.font_size))
		self.surface = self.font_renderer.render(self.text, 1, self.color)


	def update(self, event):
		pass



class zDynamicLabel(zWidget):
	def __init__(self, engine, font_size=10, font=None, color=WHITE):
		super(zDynamicLabel, self).__init__(engine)
		self.dynamic_text = lambda: "Dynamic Label"
		self.font_size = font_size
		self.font = font
		self.color = color


	def set_dynamic_text(self, dynamic_text):
		self.dynamic_text = dynamic_text


	def update(self, event):
		font_renderer = pygame.font.Font(self.font, int(self.font_size))
		self.surface = font_renderer.render(self.dynamic_text(), 1, self.color)



class zTable(zWidget):
	def __init__(self, engine, font_size=10, font=None, color=WHITE, columns=["column1", "column2"]):
		super(zTable, self).__init__(engine)
		self.font_size = font_size
		self.font = font
		self.color = color
		self.rows = {"COLUMNS":[]}
		for c in columns:
			self.rows["COLUMNS"].append(zLabel(engine, c, font_size, font, color))


	def set_pos(self, pos):
		self.position = pos
		self.rect.topleft = self.position
		c_spacing = max(len(c.text) for c in self.rows["COLUMNS"])*self.font_size
		r_spacing = self.font_size*2
		x, y = pos
		r_i = 0
		for r in self.rows:
			c_i = 0
			for t_o in self.rows[r]:
				t_o.set_pos((x+c_i*c_spacing, y+r_i*r_spacing))
				c_i += 1
			r_i += 1


	def add_row(self, newrow, rowname):
		if len(newrow) != len(self.rows["COLUMNS"]):
			print("zID:{:d} - {:s} Wrong elements in new row".format(self.zID, str(self)))
			return
		self.rows[rowname] = []
		for c in newrow:
			new_o = zLabel(self.engine, c, self.font_size, self.font, self.color)
			new_o.set_target_surface(self.target_surface)
			self.rows[rowname].append(new_o)
		self.set_pos(self.position) #update all elements positions in table since table is now different


	def del_row(self, rowname):
		for c in self.rows[rowname]:
			self.engine.delete_zID(c.zID)
		del self.rows[rowname]
		self.set_pos(self.position) #update all elements positions in table since table is now different


	def clear_rows(self):
		for r in list(self.rows.keys()):
			if r=="COLUMNS":
				continue
			for c in self.rows[r]:
				self.engine.delete_zID(c.zID)
			del self.rows[r]
		self.set_pos(self.position) #update all elements positions in table since table is now different


	def set_target_surface(self, new_target):
		self.target_surface = new_target
		for r in self.rows:
			for c in self.rows[r]:
				c.set_target_surface(new_target)


	def update(self, event):
		pass


	def draw(self, dest_surface=None):
		pass




class zButton(zWidget):

	normal = 0
	hovered = 1
	pressed = 2

	def __init__(self, engine, size, normal_color, pressed_color, hover_color=None):
		super(zButton, self).__init__(engine)
		self.size = size
		self.normal_color = normal_color
		self.pressed_color = pressed_color
		self.hover_color = hover_color
		if self.hover_color == None:
			self.hover_color = self.normal_color

		self.surface = pygame.Surface(self.size)
		self.rect = self.surface.get_rect(topleft=self.position)
		self.surface.fill(self.normal_color)

		self.status = zButton.normal
		self.perform_action = lambda: print("zID:{:d} - {:s} action performed".format(self.zID, str(self)))


	def action_performer(self, action):
		self.perform_action = action


	def change_surface_on_status(self):
		if self.status == zButton.normal:
			self.surface.fill(self.normal_color)
		elif self.status == zButton.hovered:
			self.surface.fill(self.hover_color)
		elif self.status == zButton.pressed:
			self.surface.fill(self.pressed_color)


	def update(self, event):
		mouse_pos = pygame.mouse.get_pos()
		collides = self.collidepoint(mouse_pos)
		if self.status == zButton.pressed:
			if (event.type == MOUSEBUTTONUP) and (event.button == 1):
				if collides:
					self.perform_action()
					self.status = zButton.hovered
				else:
					self.status = zButton.normal
		else:
			if collides:
				self.status = zButton.hovered
				if (event.type == MOUSEBUTTONDOWN) and (event.button == 1):
					self.status = zButton.pressed
			else:
				self.status = zButton.normal

		self.change_surface_on_status()



class zSpinner(zWidget):
	def __init__(self, engine, text, default_val, step, min_val=None, max_val=None):
		super(zSpinner, self).__init__(engine)
		self.text = text
		self.default_val = default_val
		self.value = default_val
		self.step = step
		self.min_val = min_val
		self.max_val = max_val


	def set_properties(self, size=None, bg_color=None, fg_color=None, btn_color=None):
		if size != None:
			self.size = size
		if bg_color != None:
			self.bg_color = bg_color
		if fg_color != None:
			self.fg_color = fg_color
		if btn_color != None:
			self.btn_color = btn_color

		size_x = self.size * len(self.text)
		size_y = self.size
		self.surface = pygame.Surface((size_x, size_y))
		self.rect = self.surface.get_rect(topleft=self.position)
		self.surface.fill(self.bg_color)
		z_text_draw(self.surface, self.text+' '+str(self.value), self.size, (5, 5), color=self.fg_color)



class zCheckbox(zWidget):
	def __init__(self, engine, text, default_val=False):
		super(zCheckbox, self).__init__(engine)
		self.text = text
		self.default_val = default_val
		self.value = default_val


	def set_properties(self, size=None, bg_color=None, fg_color=None, btn_color=None):
		if size != None:
			self.size = size
		if bg_color != None:
			self.bg_color = bg_color
		if fg_color != None:
			self.fg_color = fg_color
		if btn_color != None:
			self.btn_color = btn_color

		size_x = self.size * len(self.text)
		size_y = self.size
		self.surface = pygame.Surface((size_x, size_y))
		self.rect = self.surface.get_rect(topleft=self.position)
		self.surface.fill(self.bg_color)
		z_text_draw(self.surface, self.text+' '+str(self.value), self.size, (5, 5), color=self.fg_color)



class zTextField(zWidget):

	unfocused = 0
	focused = 1

	def __init__(self, engine, size, font=None, foreground=BLACK, background=WHITE, border=BLACK):
		super(zTextField, self).__init__(engine)
		self.text = ""
		self.size = size
		self.foreground = foreground
		self.background = background
		self.border = border
		self.surface = pygame.Surface(size)
		self.surface.fill(background)
		self.rect = self.surface.get_rect(topleft=self.position)
		pygame.draw.rect(self.surface, border, self.rect, 6)
		self.status = zTextField.unfocused
		self.default_text = ' '
		self.text_object = zDynamicLabel(engine, int(size[1]*0.666), font=font, color=foreground)
		self.text_object.set_dynamic_text(lambda: self.text if self.text else self.default_text)
		self.perform_action = lambda: print("zID:{:d} - {:s} writing...".format(self.zID, str(self)))


	def set_pos(self, pos):
		self.position = pos
		self.rect.topleft = self.position
		self.text_object.set_pos((pos[0]+self.size[1]/5, pos[1]+self.size[1]/5))


	def set_text(self, newtext):
		self.text = newtext if newtext else ' '


	def set_default_text(self, newtext):
		self.default_text = newtext if newtext else ' '
		#self.text_object.set_dynamic_text(lambda: self.text if self.text else self.default_text)


	def set_target_surface(self, new_target):
		self.target_surface = new_target
		self.text_object.set_target_surface(new_target)


	def action_performer(self, action):
		self.perform_action = action


	def update(self, event):
		mouse_pos = pygame.mouse.get_pos()
		collides = self.collidepoint(mouse_pos)
		if (event.type == MOUSEBUTTONDOWN) and (event.button == 1):
			if collides:
				self.status = zTextField.focused
			else:
				self.status = zTextField.unfocused
		if self.status == zTextField.focused:
			if event.type == KEYDOWN:
				key = event.key
				if 33 <= key <= 126: #alphanumeric and some symbols
					self.text += chr(key)
				elif 256 <= key <= 265: #numpad numbers
					self.text += chr(key-208)
				elif 266 <= key <= 270: #numpad symbols
					numpad = {266:'.', 267:'/', 268:'*', 269:'-', 270:'+'}
					self.text += numpad[key]
				elif key == 8: #backspace
					self.text = self.text[:-1]
				elif key == 32: #space
					self.text += ' '
				else: #all the rest
					pass
					#print(key)
				self.perform_action()



if __name__ == "__main__":
	our_engine = zEngine((800, 600))
	our_window = our_engine.get_window()
	our_window.set_refresh_behaviour(1, DARKGRAY)
	clock = pygame.time.Clock()

	# spinner = zSpinner(our_engine, "spinner", default_val=10, step=1)
	# spinner.set_pos((50, 200))
	# spinner.set_properties(size=30, bg_color=GREEN, fg_color=YELLOW, btn_color=BLUE)

	# checkbox = zCheckbox(our_engine, "checkbox", default_val=True)
	# checkbox.set_pos((50, 300))
	# checkbox.set_properties(size=30, bg_color=GREEN, fg_color=YELLOW, btn_color=BLUE)

	static_label = zLabel(our_engine, "Static Label", 25, None, MAGENTA)
	static_label.set_pos((20, 100))

	fps_label = zDynamicLabel(our_engine, 30, color=WHITE)
	fps_label.set_pos((700, 20))
	fps_label.set_dynamic_text(lambda: "%.1f FPS"%(clock.get_fps()))

	text_field = zTextField(our_engine, (100, 30))
	text_field.set_pos((70, 250))

	button = zButton(our_engine, (200, 50), WHITE, BLACK, GRAY)
	button.set_pos((70, 400))
	button.action_performer(lambda: print("text is:" + text_field.text))

	pizza_panel = zPanel(our_engine, (390, 290))
	pizza_panel.set_refresh_behaviour(1, BLUE)

	pizza_label = zLabel(our_engine, "Pizza Label", 25, None, YELLOW)
	pizza_panel.add_widget(pizza_label)
	pizza_label.set_pos((10, 10))

	pizza_text_field = zTextField(our_engine, (100, 30))
	pizza_panel.add_widget(pizza_text_field)
	pizza_text_field.set_pos((10, 40))

	pizza_button = zButton(our_engine, (200, 50), DARKRED, MAGENTA, RED)
	pizza_panel.add_widget(pizza_button)
	pizza_button.set_pos((10, 100))
	pizza_button.action_performer(lambda: print("pizza_button pressed"))

	pizza_panel.set_pos((400, 300))

	RUN = True
	while RUN:
		clock.tick(20)
		RUN = our_engine.handle_events()
		our_engine.handle_draws()
