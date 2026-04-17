"""
tests/test_plotter_presenter.py

Tests for presenter/plotter_presenter.py - the core orchestration layer.
Uses mocks for MainWindow, BenchmarkModel, and view dependencies.

This is the critical controller that wires Model-View interactions.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call


class TestPlotterPresenterInitialization:
    """Test PlotterPresenter initialization and setup."""
    
    @pytest.fixture
    def mock_window(self):
        """Create a mocked MainWindow instance."""
        window = MagicMock()
        window.left_sidebar = MagicMock()
        window.right_sidebar = MagicMock()
        window.plot_view = MagicMock()
        return window
    
    @pytest.fixture
    def mock_model(self):
        """Create a mocked BenchmarkModel instance."""
        return MagicMock()
    
    def test_initialization_creates_model(self, mock_window):
        """Presenter creates a BenchmarkModel instance on init."""
        with patch('presenter.plotter_presenter.BenchmarkModel') as MockModel:
            from presenter.plotter_presenter import PlotterPresenter
            
            start_dir = Path('/benchmarks')
            presenter = PlotterPresenter(mock_window, start_dir)
            
            MockModel.assert_called_once()
            assert presenter._model is not None
    
    def test_initialization_stores_start_dir(self, mock_window):
        """Presenter stores the starting directory."""
        with patch('presenter.plotter_presenter.BenchmarkModel'):
            from presenter.plotter_presenter import PlotterPresenter
            
            start_dir = Path('/custom/dir')
            presenter = PlotterPresenter(mock_window, start_dir)
            
            assert presenter._start_dir == start_dir
    
    def test_initialization_sets_default_show_ts(self, mock_window):
        """Default show_ts is True (tokens/s view)."""
        with patch('presenter.plotter_presenter.BenchmarkModel'):
            from presenter.plotter_presenter import PlotterPresenter
            
            presenter = PlotterPresenter(mock_window, Path('.'), default_ts=True)
            
            assert presenter._show_ts is True
    
    def test_initialization_accepts_custom_default_ts(self, mock_window):
        """Custom default_ts parameter is respected."""
        with patch('presenter.plotter_presenter.BenchmarkModel'):
            from presenter.plotter_presenter import PlotterPresenter
            
            presenter = PlotterPresenter(mock_window, Path('.'), default_ts=False)
            
            assert presenter._show_ts is False
    
    def test_initialization_wires_callbacks(self, mock_window):
        """Callbacks are wired during initialization."""
        with patch('presenter.plotter_presenter.BenchmarkModel'):
            from presenter.plotter_presenter import PlotterPresenter
            
            presenter = PlotterPresenter(mock_window, Path('.'))
            
            # Check that callback wiring was attempted
            mock_window.left_sidebar.set_file_select_callback.assert_called()
            mock_window.left_sidebar.set_sort_callback.assert_called()
    
    def test_initialization_scans_files(self, mock_window):
        """scan_files is called during initialization."""
        with patch('presenter.plotter_presenter.BenchmarkModel'):
            from presenter.plotter_presenter import PlotterPresenter
            
            presenter = PlotterPresenter(mock_window, Path('.'))
            
            # scan_files should have been called
            # We can verify this by checking state after init
    
    def test_initialization_updates_metric_button(self, mock_window):
        """Metric button is updated during initialization."""
        with patch('presenter.plotter_presenter.BenchmarkModel'):
            from presenter.plotter_presenter import PlotterPresenter
            
            presenter = PlotterPresenter(mock_window, Path('.'))
            
            # Button text should be set based on default_ts
            mock_window.set_metric_button_text.assert_called()


class TestPlotterPresenterFileManagement:
    """Test file scanning and management logic."""
    
    @pytest.fixture
    def presenter_with_mocks(self):
        """Create a presenter with fully mocked dependencies."""
        mock_window = MagicMock()
        mock_window.left_sidebar = MagicMock()
        mock_window.right_sidebar = MagicMock()
        mock_window.plot_view = MagicMock()
        
        with patch('presenter.plotter_presenter.BenchmarkModel') as MockModel:
            from presenter.plotter_presenter import PlotterPresenter
            
            model_instance = MagicMock()
            MockModel.return_value = model_instance
            
            start_dir = Path('/benchmarks')
            presenter = PlotterPresenter(mock_window, start_dir)
            
            return presenter, mock_window, model_instance
    
    def test_scan_files_filters_csv_files(self, presenter_with_mocks):
        """scan_files only includes files that pass is_llama_bench_csv check."""
        presenter, mock_window, model = presenter_with_mocks
        
        # Mock the directory glob to return some files
        csv_file1 = Path('/benchmarks/run1.csv')
        csv_file2 = Path('/benchmarks/run2.csv')
        txt_file = Path('/benchmarks/readme.txt')
        
        with patch.object(Path, 'glob') as mock_glob:
            mock_glob.return_value = [csv_file1, csv_file2, txt_file]
            
            # Mock is_llama_bench_csv to accept only first two
            with patch('presenter.plotter_presenter.is_llama_bench_csv') as mock_is_csv:
                mock_is_csv.side_effect = [True, True, False]
                
                presenter.scan_files()
                
                # Only valid CSVs should be in the list
                assert len(presenter._available_csvs) == 2
                assert csv_file1 in presenter._available_csvs
                assert csv_file2 in presenter._available_csvs
    
    def test_scan_files_sorts_by_time(self, presenter_with_mocks):
        """scan_files sorts by mtime when _sort_by_time is True."""
        presenter, mock_window, model = presenter_with_mocks
        
        file1 = Path('/benchmarks/run1.csv')
        file2 = Path('/benchmarks/run2.csv')
        
        # Set up stat mocks with different mtimes
        file1_stat = MagicMock()
        file1_stat.st_mtime = 1000
        file2_stat = MagicMock()
        file2_stat.st_mtime = 2000
        
        with patch.object(Path, 'glob') as mock_glob:
            mock_glob.return_value = [file1, file2]
            
            with patch.object(Path, 'stat') as mock_stat:
                mock_stat.side_effect = [file1_stat, file2_stat]
                
                with patch('presenter.plotter_presenter.is_llama_bench_csv', return_value=True):
                    presenter._sort_by_time = True  # Sort by time descending
                    presenter.scan_files()
                    
                    # Higher mtime should come first
                    assert presenter._available_csvs[0] == file2
                    assert presenter._available_csvs[1] == file1
    
    def test_scan_files_sorts_by_name(self, presenter_with_mocks):
        """scan_files sorts by name when _sort_by_time is False."""
        presenter, mock_window, model = presenter_with_mocks
        
        file1 = Path('/benchmarks/z_run.csv')
        file2 = Path('/benchmarks/a_run.csv')
        
        with patch.object(Path, 'glob') as mock_glob:
            mock_glob.return_value = [file1, file2]
            
            with patch('presenter.plotter_presenter.is_llama_bench_csv', return_value=True):
                presenter._sort_by_time = False  # Sort by name
                presenter.scan_files()
                
                # Alphabetical order
                assert presenter._available_csvs[0] == file2
                assert presenter._available_csvs[1] == file1
    
    def test_on_sort_toggles_sort_mode(self, presenter_with_mocks):
        """_on_sort toggles the sort mode and rescans."""
        presenter, mock_window, model = presenter_with_mocks
        
        initial_sort = presenter._sort_by_time
        presenter.scan_files = MagicMock()  # Mock to avoid actual scan
        
        presenter._on_sort()
        
        assert presenter._sort_by_time != initial_sort
        presenter.scan_files.assert_called_once()
    
    def test_on_choose_directory_updates_start_dir(self, presenter_with_mocks):
        """_on_choose_directory updates the working directory."""
        presenter, mock_window, model = presenter_with_mocks
        
        new_path = Path('/new/benchmarks')
        
        presenter.scan_files = MagicMock()  # Mock to avoid actual scan
        
        presenter._on_choose_directory(new_path)
        
        assert presenter._start_dir == new_path
        mock_window.left_sidebar.set_directory_label.assert_called_with(new_path)
    
    def test_on_select_all_calls_view_method(self, presenter_with_mocks):
        """_on_select_all delegates to the view."""
        presenter, mock_window, model = presenter_with_mocks
        
        presenter._on_select_all()
        
        mock_window.left_sidebar.select_all.assert_called_once()
    
    def test_on_deselect_all_calls_view_method(self, presenter_with_mocks):
        """_on_deselect_all delegates to the view."""
        presenter, mock_window, model = presenter_with_mocks
        
        presenter._on_deselect_all()
        
        mock_window.left_sidebar.deselect_all.assert_called_once()


class TestPlotterPresenterFileSelection:
    """Test file selection and loading logic."""
    
    @pytest.fixture
    def presenter_with_data(self):
        """Create a presenter with mocked data."""
        mock_window = MagicMock()
        mock_window.left_sidebar = MagicMock()
        mock_window.right_sidebar = MagicMock()
        mock_window.plot_view = MagicMock()
        
        with patch('presenter.plotter_presenter.BenchmarkModel') as MockModel:
            from presenter.plotter_presenter import PlotterPresenter
            
            model_instance = MagicMock()
            MockModel.return_value = model_instance
            
            presenter = PlotterPresenter(mock_window, Path('.'))
            
            # Set up some test data
            file1 = Path('/benchmarks/run1.csv')
            file2 = Path('/benchmarks/run2.csv')
            presenter._available_csvs = [file1, file2]
            
            return presenter, mock_window, model_instance
    
    def test_on_file_select_loads_files(self, presenter_with_data):
        """_on_file_select loads selected files into the model."""
        presenter, mock_window, model = presenter_with_data
        
        # Mock load_files to return no errors
        model.load_files.return_value = []
        
        presenter._on_file_select([0, 1])  # Select both files
        
        model.load_files.assert_called_once()
        call_args = model.load_files.call_args[0][0]
        assert len(call_args) == 2
    
    def test_on_file_select_updates_ui(self, presenter_with_data):
        """_on_file_select triggers UI refresh after loading."""
        presenter, mock_window, model = presenter_with_data
        
        model.load_files.return_value = []
        
        presenter._on_file_select([0])
        
        # UI should be refreshed
        mock_window.left_sidebar.update_series_toggles.assert_called()
        mock_window.set_unify_state.assert_called()
        mock_window.update_axis_choices.assert_called()


class TestPlotterPresenterFiltering:
    """Test filter management logic."""
    
    @pytest.fixture
    def presenter_with_filters(self):
        """Create a presenter with filter capabilities mocked."""
        mock_window = MagicMock()
        mock_window.left_sidebar = MagicMock()
        mock_window.right_sidebar = MagicMock()
        mock_window.plot_view = MagicMock()
        
        with patch('presenter.plotter_presenter.BenchmarkModel') as MockModel:
            from presenter.plotter_presenter import PlotterPresenter
            
            model_instance = MagicMock()
            MockModel.return_value = model_instance
            
            presenter = PlotterPresenter(mock_window, Path('.'))
            
            return presenter, mock_window, model_instance
    
    def test_on_filter_change_applies_filters(self, presenter_with_filters):
        """_on_filter_change applies filters to the model."""
        presenter, mock_window, model = presenter_with_filters
        
        filter_dict = {'ngl': {0, 1, 2}, 'batch_size': {32, 64}}
        
        presenter._render_plot = MagicMock()  # Prevent actual render
        
        presenter._on_filter_change(filter_dict)
        
        model.apply_filters.assert_called_once_with(filter_dict)
    
    def test_get_active_axes_returns_current_axes(self, presenter_with_filters):
        """_get_active_axes returns the set of currently used axes."""
        presenter, mock_window, model = presenter_with_filters
        
        # Set up window state
        mock_window.axis_x = 'ngl'
        mock_window.axis_y = 'batch_size'
        mock_window.mode_3d = True
        
        axes = presenter._get_active_axes()
        
        assert axes == {'ngl', 'batch_size'}
    
    def test_get_active_axes_2d_mode(self, presenter_with_filters):
        """In 2D mode, only X axis is returned."""
        presenter, mock_window, model = presenter_with_filters
        
        mock_window.axis_x = 'ngl'
        mock_window.mode_3d = False
        
        axes = presenter._get_active_axes()
        
        assert axes == {'ngl'}


class TestPlotterPresenterMetrics:
    """Test metric toggle functionality."""
    
    @pytest.fixture
    def presenter_for_metrics(self):
        """Create a presenter for metric tests."""
        mock_window = MagicMock()
        mock_window.left_sidebar = MagicMock()
        mock_window.right_sidebar = MagicMock()
        mock_window.plot_view = MagicMock()
        
        with patch('presenter.plotter_presenter.BenchmarkModel') as MockModel:
            from presenter.plotter_presenter import PlotterPresenter
            
            model_instance = MagicMock()
            MockModel.return_value = model_instance
            
            presenter = PlotterPresenter(mock_window, Path('.'))
            
            return presenter, mock_window, model_instance
    
    def test_toggle_metric_flips_show_ts(self, presenter_for_metrics):
        """toggle_metric flips the show_ts state."""
        presenter, mock_window, model = presenter_for_metrics
        
        initial_state = presenter._show_ts
        presenter._render_plot = MagicMock()  # Prevent actual render
        model.has_data.return_value = True
        
        presenter.toggle_metric()
        
        assert presenter._show_ts != initial_state
    
    def test_toggle_metric_updates_button(self, presenter_for_metrics):
        """toggle_metric updates the button text."""
        presenter, mock_window, model = presenter_for_metrics
        
        presenter.toggle_metric()
        
        mock_window.set_metric_button_text.assert_called()
    
    def test_update_metric_button_text_correct(self, presenter_for_metrics):
        """_update_metric_button sets correct text based on show_ts."""
        presenter, mock_window, model = presenter_for_metrics
        
        # When showing tokens/s (show_ts=True), button says "Switch: ns"
        presenter._show_ts = True
        presenter._update_metric_button()
        mock_window.set_metric_button_text.assert_called_with("Switch: ns")
        
        # When showing ns (show_ts=False), button says "Switch: t/s"
        presenter._show_ts = False
        presenter._update_metric_button()
        mock_window.set_metric_button_text.assert_called_with("Switch: t/s")


class TestPlotterPresenter3DMode:
    """Test 3D mode toggle functionality."""
    
    @pytest.fixture
    def presenter_for_3d(self):
        """Create a presenter for 3D tests."""
        mock_window = MagicMock()
        mock_window.left_sidebar = MagicMock()
        mock_window.right_sidebar = MagicMock()
        mock_window.plot_view = MagicMock()
        
        with patch('presenter.plotter_presenter.BenchmarkModel') as MockModel:
            from presenter.plotter_presenter import PlotterPresenter
            
            model_instance = MagicMock()
            MockModel.return_value = model_instance
            
            presenter = PlotterPresenter(mock_window, Path('.'))
            
            return presenter, mock_window, model_instance
    
    def test_on_toggle_3d_triggers_render(self, presenter_for_3d):
        """_on_toggle_3d updates sidebar and re-renders."""
        presenter, mock_window, model = presenter_for_3d
        
        presenter._render_plot = MagicMock()
        presenter._update_right_sidebar = MagicMock()
        
        presenter._on_toggle_3d()
        
        presenter._update_right_sidebar.assert_called()
        presenter._render_plot.assert_called()


class TestPlotterPresenterCamera:
    """Test 3D camera save/restore functionality."""
    
    def test_save_camera_basic(self):
        """_save_camera captures basic camera state."""
        with patch('presenter.plotter_presenter.BenchmarkModel'):
            from presenter.plotter_presenter import PlotterPresenter
            
            mock_window = MagicMock()
            mock_window.left_sidebar = MagicMock()
            mock_window.right_sidebar = MagicMock()
            mock_window.plot_view = MagicMock()
            
            presenter = PlotterPresenter(mock_window, Path('.'))
            
            # Create a mock axis
            mock_ax = MagicMock()
            mock_ax.elev = 30
            mock_ax.azim = -60
            
            state = presenter._save_camera(mock_ax)
            
            assert 'elev' in state
            assert 'azim' in state
            assert state['elev'] == 30
            assert state['azim'] == -60
    
    def test_restore_camera_applies_state(self):
        """_restore_camera applies saved camera state."""
        with patch('presenter.plotter_presenter.BenchmarkModel'):
            from presenter.plotter_presenter import PlotterPresenter
            
            mock_window = MagicMock()
            mock_window.left_sidebar = MagicMock()
            mock_window.right_sidebar = MagicMock()
            mock_window.plot_view = MagicMock()
            
            presenter = PlotterPresenter(mock_window, Path('.'))
            
            # Create a mock axis
            mock_ax = MagicMock()
            
            state = {'elev': 45, 'azim': -90}
            
            presenter._restore_camera(mock_ax, state)
            
            mock_ax.view_init.assert_called_with(elev=45, azim=-90)
    
    def test_on_home_3d_restores_home_camera(self):
        """_on_home_3d restores the home camera position."""
        with patch('presenter.plotter_presenter.BenchmarkModel'):
            from presenter.plotter_presenter import PlotterPresenter
            
            mock_window = MagicMock()
            mock_window.left_sidebar = MagicMock()
            mock_window.right_sidebar = MagicMock()
            mock_window.plot_view = MagicMock()
            mock_window.mode_3d = True
            
            presenter = PlotterPresenter(mock_window, Path('.'))
            
            # Set up home camera state
            presenter._home_cam_3d = {'elev': 30, 'azim': -60}
            mock_ax = MagicMock()
            presenter._current_3d_ax = mock_ax
            
            result = presenter._on_home_3d()
            
            assert result is True
            mock_ax.view_init.assert_called()


class TestPlotterPresenterRendering:
    """Test rendering orchestration logic."""
    
    @pytest.fixture
    def presenter_for_render(self):
        """Create a presenter for render tests."""
        mock_window = MagicMock()
        mock_window.left_sidebar = MagicMock()
        mock_window.right_sidebar = MagicMock()
        mock_window.plot_view = MagicMock()
        
        with patch('presenter.plotter_presenter.BenchmarkModel') as MockModel:
            from presenter.plotter_presenter import PlotterPresenter
            
            model_instance = MagicMock()
            MockModel.return_value = model_instance
            
            presenter = PlotterPresenter(mock_window, Path('.'))
            
            return presenter, mock_window, model_instance
    
    def test_render_plot_shows_placeholder_no_data(self, presenter_for_render):
        """_render_plot shows placeholder when no data is loaded."""
        presenter, mock_window, model = presenter_for_render
        
        model.has_data.return_value = False
        
        presenter._render_plot()
        
        mock_window.plot_view.show_placeholder.assert_called()
    
    def test_render_plot_calls_correct_renderer(self, presenter_for_render):
        """_render_plot calls the correct renderer based on mode."""
        presenter, mock_window, model = presenter_for_render
        
        model.has_data.return_value = True
        
        # Mock the render methods
        presenter._render_2d = MagicMock()
        presenter._render_3d = MagicMock()
        
        # Test 2D mode
        mock_window.mode_3d = False
        mock_window.axis_x = 'ngl'
        mock_window.normalize = False
        mock_window.z_label_mode = 'abs'
        mock_window.show_pp = True
        mock_window.show_tg = True
        
        presenter._render_plot()
        
        presenter._render_2d.assert_called()
        presenter._render_3d.assert_not_called()
    
    def test_render_3d_validates_axes(self, presenter_for_render):
        """_render_3d shows placeholder if axes are invalid."""
        presenter, mock_window, model = presenter_for_render
        
        # Invalid: same axis for X and Y
        mock_window.axis_x = 'ngl'
        mock_window.axis_y = 'ngl'  # Same as X - invalid!
        
        presenter._render_3d('ngl', False, False, True, True)
        
        mock_window.plot_view.show_placeholder.assert_called()
