from gi.repository import Gtk, GLib
from collections import namedtuple

escape_text = GLib.markup_escape_text

Option = namedtuple("Option", "name button label error")

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
        widgets =  [widget1]
        if widget2:
            widgets.append(widget2)
        return widgets
    
    def clear(self):
        for widget in self.body.get_children():
            self.body.remove(widget)
        self.line = 0

class LoginPage(Page):
    def __init__(self, password_reset_url, sign_up_url):
        Page.__init__(self, "Repository Access")
        
        self.option_anonymous = Gtk.RadioButton.new_with_label_from_widget(None, "Anonymous Access")
        self.option_account = Gtk.RadioButton.new_with_label_from_widget(self.option_anonymous, "Access with Tiliado Account")
        self.option_anonymous.connect("toggled", self.on_button_toggled)
        self.option_account.connect("toggled", self.on_button_toggled)
        self.add_row(self.option_anonymous)
        self.add_row(self.option_account)
        self.password_reset_url = password_reset_url
        self.sign_up_url = sign_up_url
        self.login_widgets = []
        
        self.message = Gtk.Label(label="", margin_bottom=15, justify=Gtk.Justification.CENTER)
        self.set_error()
        self.login_widgets.extend(self.add_row(self.message))
        self.username_entry = Gtk.Entry(hexpand=True, halign=Gtk.Align.CENTER)
        self.login_widgets.extend(self.add_row(Gtk.Label(label="Username:"), self.username_entry))
        self.password_entry = Gtk.Entry(hexpand=True, halign=Gtk.Align.CENTER, input_purpose=Gtk.InputPurpose.PASSWORD, visibility=False)
        self.login_widgets.extend(self.add_row(Gtk.Label(label="Password:"), self.password_entry))
        self.login_widgets.extend(self.add_row(Gtk.Label(label='<a href="{}">Forgot password?</a>'.format(password_reset_url), use_markup=True, margin_top=15)))
        self.login_widgets.extend(self.add_row(Gtk.Label(label='<a href="{}">Don\'t have an account?</a>'.format(sign_up_url), use_markup=True)))
        
        self.quit_button = Gtk.Button.new_with_label("Quit")
        self.buttons.add(self.quit_button)
        self.sign_in_button = Gtk.Button.new_with_label("Continue")
        self.buttons.add(self.sign_in_button)
        
        self.show_all()
        for w in self.login_widgets:
            w.hide()
    
    def set_error(self, text=None):
        self.message.set_label(text if text is not None else \
        "Fill in credentials for your Tiliado Account.")
        self.message.show()
    
    def set_widgets_sensitive(self, sensitive):
        for w in self.username_entry, self.password_entry, self.sign_in_button:
            w.set_sensitive(sensitive)
    
    def on_button_toggled(self, button):
        if button.get_active():
            visible = button == self.option_account
            for w in self.login_widgets:
                w.set_visible(visible)

class RepositoriesPage(Page):
    def __init__(self):
        Page.__init__(self, "Tiliado Repositories")
        
        self.back_button = Gtk.Button.new_with_label("Back")
        self.buttons.add(self.back_button)
        self.ok_button = Gtk.Button.new_with_label("Continue")
        self.buttons.add(self.ok_button)
        self.repo = None
        self.ok_button.set_sensitive(False)
        self.show_all()
    
    def clear(self):
        Page.clear(self)
        self.repo = None
        self.ok_button.set_sensitive(False)
    
    def set_repositories(self, repositories):
        self.repositories = repositories
        self.clear()
        self.ok_button.set_sensitive(False)
        
        group = None
        for index, repo in enumerate(repositories):
            button = Gtk.RadioButton.new_with_label_from_widget(group, repo["label"])
            button.set_vexpand(False)
            button.connect("toggled", self.on_button_toggled, index)
            if not group:
                group = button
                self.repo = repo
                self.ok_button.set_sensitive(True)
                button.set_active(True)
        
            self.add_row(button)
            button.show()
        
    def on_button_toggled(self, button, index):
        if button.get_active():
            self.repo = self.repositories[index]
            self.ok_button.set_sensitive(True)

class ComponentsPage(Page):
    def __init__(self, dist=None):
        Page.__init__(self, "Components")
        
        self.back_button = Gtk.Button.new_with_label("Back")
        self.buttons.add(self.back_button)
        self.ok_button = Gtk.Button.new_with_label("Continue")
        self.buttons.add(self.ok_button)
        self.ok_button.set_sensitive(False)
        
        self.enabled_components = set()
        self.dist = dist
        self.add_row(Gtk.Label(label="Choose your distribution and repository component.", margin_bottom=5))
        self.dist_entry = Gtk.ComboBoxText()
        self.dist_entry.connect("changed", self.on_dist_entry_changed)
        self.dist_label = Gtk.Label(label="Distribution:")
        self.add_row(self.dist_label, self.dist_entry)
        self.top_label = Gtk.Label(use_markup=True)
        self.add_row(self.top_label)
        
        self.option_widgets = []
        self.clear()
        self.show_all()
    
    def clear(self):
        for opt in self.option_widgets:
            opt.button.disconnect_by_func(self.on_button_toggled)
            self.body.remove(opt.button)
            self.body.remove(opt.label)
            self.line -= 2
            if opt.error:
                self.body.remove(opt.error)
                self.line -= 1
            
        self.option_widgets = []
        self.enabled_components.clear()
        self.ok_button.set_sensitive(False)
    
    def can_access(self, component):
        groups = component.groups
        for group in self.user_groups:
            if group in groups:
                return True
        
        return False
        
    def set_data(self, user_groups, options):
        self.user_groups = user_groups
        self.options = options
        self.clear()
        self.ok_button.set_sensitive(False)
        if options:
            self.top_label.hide()
            self.dist_entry.show()
            self.dist_label.show()
            
            dists = sorted([[dist.label, dist.name] for dist in options.values()])
            self.dist_model = Gtk.ListStore(str, str)
            for dist in dists:
                self.dist_model.append(dist)
            
            self.dist_entry.set_model(self.dist_model)
            self.dist_entry.set_entry_text_column(0)
            self.dist_entry.set_id_column(1)
            if self.dist is None or not self.dist_entry.set_active_id(self.dist):
                print("Unknown dist: %r" % self.dist)
                self.dist_entry.set_active(0)
        else:
            self.dist_entry.hide()
            self.dist_label.hide()
            self.top_label.set_markup("<b>There are no components in this repository.</b>")
            self.top_label.show()
    
    def _create_option(self, components, pk, radio_group, active=None, indent=0):
        c = components.get(pk)
        if not c:
            return None
        
        access = self.can_access(c)
        desc = Gtk.Label.new(c.desc)
        
        already_selected = False
        if radio_group:
            for item in radio_group.get_group():
                if item.get_sensitive() and item.get_active():
                    already_selected = True
                    break
        
        button = Gtk.RadioButton.new_with_label_from_widget(radio_group, "<b>{}</b>".format(escape_text(c.label)))
        if access:
            error = None
            if not already_selected:
                self.enabled_components.clear()
                self.enabled_components.add(pk)
                button.set_active(True)
        else:
            button.set_sensitive(False)
            groups = sorted(list(c.groups.values()))
            if len(groups) > 1:
                groups = " and ".join((", ".join(groups[:-1]), groups[-1]))
            else:
                groups = groups[0]
            error = Gtk.Label.new("<i>Available only for {}.</i>".format(escape_text(groups)))
            error.set_use_markup(True)
            error.set_margin_left(indent + 25)
            
            
        if indent:
            button.set_margin_left(indent)
        
        self.add_row(button)
        button.get_child().set_use_markup(True)
        button.connect("toggled", self.on_button_toggled, pk)
        button.show()
        self.add_row(desc)
        desc.set_halign(Gtk.Align.START)
        desc.set_margin_left(indent + 25)
        desc.show()
        
        if error:
            error.set_halign(Gtk.Align.START)
            error.show()
            self.add_row(error)
        
        option = Option(pk, button, desc, error)
        self.option_widgets.append(option)
        self._update_ok_button()
        return option
    
    def _update_options(self):
        self.clear()
        components = self.options[self.dist].components
        
        group = None
        for key in "stable", "hotfix", "beta", "devel":
            option = self._create_option(components, key, group)
            if option:
                group = option.button
        
        self._update_ok_button()
    
    def _update_ok_button(self):
        self.ok_button.set_sensitive(bool(self.dist and self.enabled_components))
    
    def on_dist_entry_changed(self, combobox):
        self.dist = combobox.get_active_id()
        self._update_options()
            
    def on_button_toggled(self, button, key):
        if button.get_active():
            self.enabled_components.clear()
            self.enabled_components.add(key)
        
        self._update_ok_button()

class ProductsPage(Page):
    def __init__(self):
        Page.__init__(self, "Packages")
        self.back_button = Gtk.Button.new_with_label("Back")
        self.buttons.add(self.back_button)
        self.ok_button = Gtk.Button.new_with_label("Continue")
        self.buttons.add(self.ok_button)
        self.selected_products = set()
        self._buttons = []
        self.show_all()
    
    def clear(self):
        for button in self._buttons:
            button.disconnect_by_func(self.on_button_toggled)
        self.selected_products.clear()
        Page.clear(self)
    
    def set_data(self, products):
        self.clear()
        top_label = Gtk.Label(label="Choose which packages do you want to install.", margin_bottom=5)
        top_label.show()
        self.add_row(top_label)
        
        for p in sorted(products, key=lambda p: p["name"]):
            button = Gtk.CheckButton.new_with_label("<b>{}</b>".format(escape_text(p["name"])))
            button.get_child().set_use_markup(True)
            button.connect("toggled", self.on_button_toggled, p["id"])
            button.set_active(p["auto_select"])
            button.show()
            self._buttons.append(button)
            self.add_row(button)
            desc = Gtk.Label.new(p["description"])
            desc.set_halign(Gtk.Align.START)
            desc.set_margin_left(25)
            desc.show()
            self.add_row(desc)
    
    def on_button_toggled(self, button, key):
        if button.get_active():
            self.selected_products.add(key)
        else:
            self.selected_products.remove(key)
        
class SummaryPage(Page):
    def __init__(self, ):
        Page.__init__(self, "Summary")
        
        self.back_button = Gtk.Button.new_with_label("Back")
        self.buttons.add(self.back_button)
        self.ok_button = Gtk.Button.new_with_label("Install")
        self.buttons.add(self.ok_button)
        self.show_all()
    
    def set_data(self, repo, products):
        products.sort()
        if len(products) >= 2:
            products = " and ".join((", ".join(products[:-1]), products[-1]))
        elif products:
            products = products[0]
        else:
            products = None
        
        self.clear()
        self.add_row(Gtk.Label(label="Tiliado Repositories Installer will carry out these actions:", halign=Gtk.Align.START, margin_bottom=15))
        bullet = "\u2022"
        
        lines = []
        if products:
            lines.append('Try to remove old packages to prevent conflicts.')
        
        lines.extend((
            'Add {} repository to your software sources.'.format(repo),
            'Import signing key for {} repository.'.format(repo),
            'Update package database.',
        ))
        
        if products:
            lines.append('Install {}.'.format(products))
        
        for line in lines:
            self.add_row(Gtk.Label(label=bullet), Gtk.Label(label=line, halign=Gtk.Align.START))
        
        self.add_row(Gtk.Label(label="<b>You will be asked for authorization of a privileged user.</b>",
            halign=Gtk.Align.START, margin_top=15, use_markup=True))
        self.show_all()

class ProgressPage(Page):
    def __init__(self, ):
        Page.__init__(self, "Installation progress")
        self.body.set_vexpand(True)
        self.body.set_hexpand(True)
        self.body.set_halign(Gtk.Align.FILL)
        self.body.set_valign(Gtk.Align.FILL)
        
        self.message = Gtk.Label(label="", use_markup=True, no_show_all=True)
        self.add_row(self.message)
        self.output = Gtk.TextView(vexpand=True, hexpand=True, editable=False)
        self.buffer = self.output.get_buffer()
        scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        scroll.add(self.output)
        self.add_row(scroll)
        
        self.back_button = Gtk.Button.new_with_label("Back")
        self.buttons.add(self.back_button)
        self.quit_button = Gtk.Button.new_with_label("Quit")
        self.buttons.add(self.quit_button)
        
        self.show_all()
    
    def clear(self):
        self.set_message("Installation is in progress...")
        self.buffer.set_text("")
    
    def write(self, data):
        buf = self.buffer
        end = buf.get_end_iter()
        buf.insert(end, data)
        end = buf.get_end_iter()
        self.output.scroll_to_iter(end, 0.0, False, 0, 0);
        while Gtk.events_pending():
            Gtk.main_iteration()
    
    def set_message(self, text=None):
        if text:
            self.message.set_label(text)
            self.message.show()
        else:
            self.message.hide()
    
    def set_sensitive(self, sensitive):
        for w in (self.back_button, self.quit_button):
            w.set_sensitive(sensitive)
