import pygame
from pygame.locals import *
import pygame_menu
import random
import math

pygame.init()

# frames per second
fps = 120

# width and height of each cell
cell_size = 30

# height of the panel containing the timer and flag count
top_panel_height = 30

# values for mouse click event
left_mouse_click = 1
right_mouse_click = 3

# font for displaying clues, time, and flag count
font = pygame.font.Font(pygame.font.get_default_font(), 18)

# define colors for displaying clues
clue_colors = ['', 'blue', 'green', 'red', 'purple', 'maroon', 'turquoise', 'black', 'dimgray']

class Game:

	def __init__(self):
		
		self.set_difficulty('beginner')
		self.setup_window()

		# declare the menus and display the new game menu
		self.new_game_menu = None
		self.gameover_menu = None
		self.display_new_game_menu()

	def set_difficulty(self, difficulty):
		
		if difficulty == 'beginner':
			self.size = {'rows': 8, 'cols': 8}
			self.num_mines = 10
		elif difficulty == 'intermediate':
			self.size = {'rows': 16, 'cols': 16}
			self.num_mines = 40
		elif difficulty == 'expert':
			self.size = {'rows': 16, 'cols': 30}
			self.num_mines = 99

	def setup_window(self):
		width = cell_size * self.size['cols']
		height = cell_size * self.size['rows'] + top_panel_height
		self.window = pygame.display.set_mode((width, height))
		pygame.display.set_caption('Minesweeper')

	def new_game(self, difficulty):
		
		self.gameover = False

		# set the difficulty and reset the window
		self.set_difficulty(difficulty)
		self.setup_window()

		# keep track of cells using a dictionary
		self.cells = dict()
		self.create_cells()

		# keep track of how many cells have been revealed
		self.revealed_count = 0

		# keep track of how many flags have been used
		self.flag_count = 0

		# game timer
		self.time = 0

		# create a user event for updating time value
		self.timer_event = pygame.USEREVENT + 1

		# call this event every 1 second
		pygame.time.set_timer(self.timer_event, 1000)

		# hide the new game menu
		self.new_game_menu.disable()

		# hide the game over menu
		if self.gameover_menu is not None:
			self.gameover_menu.disable()

	def display_new_game_menu(self):
		my_theme = pygame_menu.themes.THEME_BLUE
		my_theme.title_font_size = 18
		my_theme.widget_font_size = 12
		self.new_game_menu = pygame_menu.Menu('New Game', 150, 150, theme = my_theme)
		self.new_game_menu.add.button('Beginner', lambda s=self : s.new_game('beginner'))
		self.new_game_menu.add.button('Intermediate', lambda s=self : s.new_game('intermediate'))
		self.new_game_menu.add.button('Expert', lambda s=self : s.new_game('expert'))
		self.new_game_menu.mainloop(self.window, fps_limit = fps)

	def display_gameover_menu(self, heading):
		my_theme = pygame_menu.themes.THEME_BLUE
		my_theme.title_font_size = 18
		my_theme.widget_font_size = 12
		self.gameover_menu = pygame_menu.Menu(heading, 150, 150, theme = my_theme)
		if heading == 'Game Over':
			self.gameover_menu.add.label('You clicked on a mine!')
		elif heading == 'Game Cleared':
			self.gameover_menu.add.label(f'Clear Time: {self.time} seconds')
		self.gameover_menu.add.vertical_margin(30)
		self.gameover_menu.add.button('Play Again', lambda s=self : s.display_new_game_menu())
		self.gameover_menu.mainloop(self.window, fps_limit = fps)

	def create_cells(self):
		
		# create rows and columns of cells
		for row in range(self.size['rows']):
			for col in range(self.size['cols']):

				cell = Cell(row, col)

				# add to dictionary using (row, col) as the key
				self.cells[(row, col)] = cell

	def draw_cells(self):
		for (row, col) in self.cells:
			cell = self.cells[(row, col)]
			cell.draw(self.window)

	def draw_top_panel(self):
		
		# create the top panel
		top_panel = Rect(0, 0, self.window.get_width(), top_panel_height)
		dark_blue = (9, 76, 158)
		pygame.draw.rect(self.window, dark_blue, top_panel)

		# display the elapsed time
		time_text = font.render(f'Time: {str(self.time)}', True, (255, 255, 255))
		time_rect = time_text.get_rect()
		time_rect.center = (40, top_panel_height // 2)
		self.window.blit(time_text, time_rect)

		# display the flag count
		flag_count_text = font.render(f'Flags: {str(self.flag_count)}', True, (255, 255, 255))
		flag_count_rect = flag_count_text.get_rect()
		flag_count_rect.center = (self.window.get_width() - 40, top_panel_height // 2)
		self.window.blit(flag_count_text, flag_count_rect)

	def get_clicked_cell(self, click_location):
		
		# iterate through every cell
		for (row, col) in self.cells:
			cell = self.cells[(row, col)]

			# check if that cell was clicked
			if cell.collidepoint(click_location):
				return cell

		# no cell was clicked
		return None

	def left_click(self, click_location):
		
		# do nothing if the game is over
		if self.gameover:
			return

		clicked_cell = self.get_clicked_cell(click_location)

		if clicked_cell is not None:

			# check if this is the first click of the game
			if self.revealed_count == 0:
				self.place_mines(clicked_cell)
				self.update_clues()

			# reveal the cell and increment the revealed_count
			self.revealed_count += clicked_cell.reveal(self.cells)

			# game is over if the clicked cell has a mine
			if clicked_cell.has_mine:
				self.gameover = True

			# check if the game is cleared
			if self.revealed_count == self.size['rows'] * self.size['cols'] - self.num_mines:
				self.gameover = True
				self.display_gameover_menu('Game Cleared')

	def right_click(self, click_location):
		
		# do nothing if the game is over
		if self.gameover:
			return

		clicked_cell = self.get_clicked_cell(click_location)

		# can only right click if cell has not been revealed yet
		if clicked_cell is not None and clicked_cell.state != 'revealed':

			# toggle between flagged and hidden states
			if clicked_cell.state == 'flagged':
				clicked_cell.state = 'hidden'
				self.flag_count -= 1
			else:
				clicked_cell.state = 'flagged'
				self.flag_count += 1

	def place_mines(self, clicked_cell):
		
		# create mines at random locations
		mine_count = 0
		while mine_count < self.num_mines:
			row = random.randint(0, self.size['rows'] - 1)
			col = random.randint(0, self.size['cols'] - 1)
			mine_cell = self.cells[(row, col)]

			# calculate distance between mine and the clicked cell
			distance = math.sqrt((row - clicked_cell.row) ** 2 + (col - clicked_cell.col) ** 2)

			# place mine only if it's more than two cells away from the clicked cell
			# and the location doesn't already have a mine
			if distance > 2 and mine_cell.has_mine == False:
				mine_cell.has_mine = True
				mine_count += 1

	def update_clues(self):
		
		# iterate through every cell
		for (row, col) in self.cells:
			cell = self.cells[(row, col)]

			# check the surrounding cells
			for adjacent_row in range(row - 1, row + 2):
				for adjacent_col in range(col - 1, col + 2):

					# no need to check same cell
					if cell.row == adjacent_row and cell.col == adjacent_col:
						continue

					# check if adjacent location has a mine
					if (adjacent_row, adjacent_col) in self.cells:
						adjacent_cell = self.cells[(adjacent_row, adjacent_col)]
						if adjacent_cell.has_mine:
							cell.clue += 1

	def reveal_all_cells(self):
		for (row, col) in self.cells:
			cell = self.cells[(row, col)]
			self.revealed_count += cell.reveal(self.cells)

class Cell(pygame.Rect):

	def __init__(self, row, col):
		
		self.row = row
		self.col = col

		self.left = col * cell_size
		self.top = row * cell_size + top_panel_height
		self.width = cell_size
		self.height = cell_size

		# state of the cell (hidden, revealed, or flagged)
		self.state = 'hidden'

		# is there a mine in this cell
		self.has_mine = False

		# how many mines surround this cell
		self.clue = 0

	def draw(self, window):
		
		# make cells have alternating background colors
		if (self.row + self.col) % 2 == 0:
			bg_color = (98, 159, 222)
		else:
			bg_color = (42, 106, 184)
		pygame.draw.rect(window, bg_color, self)

		# display the mine or the clue
		if self.state == 'revealed':

			# display the mine
			if self.has_mine:
				pygame.draw.rect(window, 'crimson', self)
				center_x = self.left + cell_size // 2
				center_y = self.top + cell_size // 2
				pygame.draw.circle(window, 'black', (center_x, center_y), cell_size / 4)

			else:

				# make the revealed cells have alternating background colors
				if (self.row + self.col) % 2 == 0:
					pygame.draw.rect(window, 'azure1', self)
				else:
					pygame.draw.rect(window, 'azure3', self)

				# display the clue
				if self.clue > 0:
					text = font.render(str(self.clue), True, clue_colors[self.clue])
					text_rect = text.get_rect()
					center_x = self.left + cell_size // 2
					center_y = self.top + cell_size // 2
					text_rect.center = (center_x, center_y)
					window.blit(text, text_rect)

		# display the flag
		if self.state == 'flagged':

			# draw the triangular flag
			point1 = (self.left + cell_size // 3, self.top + cell_size // 5)
			point2 = (self.left + cell_size // 3, self.top + cell_size // 2)
			point3 = (self.left + cell_size // 3 * 2, self.top + cell_size // 3)
			pygame.draw.polygon(window, 'red', (point1, point2, point3))

			# draw the pole
			start = (self.left + cell_size // 3, self.top + cell_size // 5)
			end = (self.left + cell_size // 3, self.top + cell_size * 4 // 5)
			pygame.draw.line(window, 'black', start, end)

		# top border
		start = (self.left, self.top)
		end = (self.left + cell_size, self.top)
		pygame.draw.line(window, 'black', start, end)

		# right border
		start = (self.left + cell_size, self.top)
		end = (self.left + cell_size, self.top + cell_size)
		pygame.draw.line(window, 'black', start, end)

		# bottom border
		start = (self.left + cell_size, self.top + cell_size)
		end = (self.left, self.top + cell_size)
		pygame.draw.line(window, 'black', start, end)

		# left border
		start = (self.left, self.top + cell_size)
		end = (self.left, self.top)
		pygame.draw.line(window, 'black', start, end)

	def reveal(self, cells):
		
		# do nothing if cell is already revealed or flagged
		if self.state == 'revealed' or self.state == 'flagged':
			return 0

		# change state to revealed
		self.state = 'revealed'
		revealed_count = 1

		# if there are no mines surrounding this cell
		# recursively reveal surrounding cells
		if self.clue == 0:

			for adjacent_row in range(self.row - 1, self.row + 2):
				for adjacent_col in range(self.col - 1, self.col + 2):

					if (adjacent_row, adjacent_col) in cells:
						adjacent_cell = cells[(adjacent_row, adjacent_col)]
						revealed_count += adjacent_cell.reveal(cells)

		return revealed_count

def main():

	# create the game
	game = Game()

	# game loop
	clock = pygame.time.Clock()
	running = True
	while running:

		clock.tick(fps)

		for event in pygame.event.get():
			if event.type == QUIT:
				running = False

			# increment the game time
			if event.type == game.timer_event and not game.gameover:
				game.time += 1

			# handle mouse clicks
			if event.type == MOUSEBUTTONDOWN:
				if event.button == left_mouse_click:
					game.left_click(event.pos)
				elif event.button == right_mouse_click:
					game.right_click(event.pos)


		game.draw_top_panel()
		game.draw_cells()

		pygame.display.update()

		# check if the game is over
		if game.gameover:
			game.reveal_all_cells()
			game.draw_cells()
			pygame.display.update()

			# wait 3 seconds
			pygame.time.wait(3000)
			game.display_gameover_menu('Game Over')
	
	pygame.quit()

if __name__ == '__main__':
	main()