from gi.repository import Gtk

class Page(Gtk.Grid):
    def __init__(self, header):
        Gtk.Grid.__init__(self, expand=True, margin=10, orientation=Gtk.Orientation.VERTICAL, row_spacing=15, hexpand=True, vexpand=True)
        self.header = Gtk.Label(label="<big><b>%s</b></big>" % header, use_markup=True, hexpand=True, vexpand=False, margin_top=15)
        self.body = Gtk.Grid(row_spacing=10, column_spacing=10, hexpand=True, vexpand=True, valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER)
        self.buttons = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL, layout_style=Gtk.ButtonBoxStyle.EDGE, hexpand=True, vexpand=False)
        self.attach(self.header, 0, 0, 1, 1)
        self.attach(self.body, 0, 1, 1, 1)
        self.attach(self.buttons, 0, 2, 1, 1)
        self.line = 0
    
    def add_row(self, widget1, widget2=None):
        if widget2 is None:
            self.body.attach(widget1, 0, self.line, 2, 1)
            self.line += 1
        else:
            if widget1 is not None:
                self.body.attach(widget1, 0, self.line, 1, 1)
            if isinstance(widget2, (tuple, list)):
                for widget in widget2:
                    self.body.attach(widget, 1, self.line, 1, 1)
                    self.line += 1
            else:
                self.body.attach(widget2, 1, self.line, 1, 1)
                self.line += 1

class LoginPage(Page):
    def __init__(self, password_reset_url, sign_up_url):
        Page.__init__(self, "Tiliado Account")
        
        self.password_reset_url = password_reset_url
        self.sign_up_url = sign_up_url
        
        self.message = Gtk.Label(label="", margin_bottom=15, justify=Gtk.Justification.CENTER)
        self.set_error()
        self.add_row(self.message)
        self.username_entry = Gtk.Entry(hexpand=True, halign=Gtk.Align.CENTER)
        self.add_row(Gtk.Label(label="Username:"), self.username_entry)
        self.password_entry = Gtk.Entry(hexpand=True, halign=Gtk.Align.CENTER, input_purpose=Gtk.InputPurpose.PASSWORD, visibility=False)
        self.add_row(Gtk.Label(label="Password:"), self.password_entry)
        self.add_row(Gtk.Label(label='<a href="{}">Forgot password?</a>'.format(password_reset_url), use_markup=True, margin_top=15))
        self.add_row(Gtk.Label(label='<a href="{}">Don\'t have an account?</a>'.format(sign_up_url), use_markup=True))
        
        self.quit_button = Gtk.Button.new_with_label("Quit")
        self.buttons.add(self.quit_button)
        self.sign_in_button = Gtk.Button.new_with_label("Sign in")
        self.buttons.add(self.sign_in_button)
        
        self.show_all()
    
    def set_error(self, text=None):
        self.message.set_label(text if text is not None else \
        "Fill in credentials for your Tiliado Account to access\nTiliado Repositories.")
        self.message.show()
    
    def set_widgets_sensitive(self, sensitive):
        for w in self.username_entry, self.password_entry, self.sign_in_button:
            w.set_sensitive(sensitive)
