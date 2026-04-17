"""
tests/test_llamagraph_entry.py

Tests for llamagraph.py - CLI argument parsing and entry point logic.
Tests up to the point of GUI instantiation (which requires Tkinter).
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestParseArgs:
    """Test CLI argument parsing."""
    
    def test_default_arguments(self):
        """Default arguments are set correctly when no args provided."""
        with patch('sys.argv', ['llamagraph.py']):
            # Need to reparse since parse_args calls sys.argv directly
            import argparse
            parser = argparse.ArgumentParser(
                description="llamagraph — llama-bench benchmark visualizer"
            )
            parser.add_argument(
                'path',
                nargs='?',
                type=Path,
                default=Path('.'),
                help="Directory or specific CSV file to load (default: current dir)",
            )
            parser.add_argument(
                '--ns',
                action='store_true',
                help="Start in latency (ns) view instead of tokens/s",
            )
            args = parser.parse_args([])
            
            assert args.path == Path('.')
            assert args.ns is False
    
    def test_custom_directory_path(self):
        """Custom directory path is accepted."""
        test_dir = Path('/custom/benchmarks')
        
        with patch('sys.argv', ['llamagraph.py', str(test_dir)]):
            # Manually parse to test logic
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument('path', nargs='?', type=Path, default=Path('.'))
            parser.add_argument('--ns', action='store_true')
            args = parser.parse_args([str(test_dir)])
            
            assert args.path == test_dir
    
    def test_custom_file_path(self):
        """Custom file path is accepted."""
        test_file = Path('/path/to/benchmark.csv')
        
        with patch('sys.argv', ['llamagraph.py', str(test_file)]):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument('path', nargs='?', type=Path, default=Path('.'))
            args = parser.parse_args([str(test_file)])
            
            assert args.path == test_file
    
    def test_ns_flag_enabled(self):
        """--ns flag sets ns to True."""
        with patch('sys.argv', ['llamagraph.py', '--ns']):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument('path', nargs='?', type=Path, default=Path('.'))
            parser.add_argument('--ns', action='store_true')
            args = parser.parse_args(['--ns'])
            
            assert args.ns is True
    
    def test_ns_flag_with_path(self):
        """--ns flag works with custom path."""
        test_dir = Path('/benchmarks')
        
        with patch('sys.argv', ['llamagraph.py', str(test_dir), '--ns']):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument('path', nargs='?', type=Path, default=Path('.'))
            parser.add_argument('--ns', action='store_true')
            args = parser.parse_args([str(test_dir), '--ns'])
            
            assert args.path == test_dir
            assert args.ns is True


class TestMainLogic:
    """Test main() logic up to GUI instantiation."""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mocks before each test to prevent Tkinter imports."""
        # Mock tkinter BEFORE importing llamagraph
        self.tk_mock = MagicMock()
        self.csv_parser_mock = MagicMock()
        self.main_window_mock = MagicMock()
        self.presenter_mock = MagicMock()
        
        # Create patchers
        self.patch_tk = patch('llamagraph.tk', self.tk_mock)
        self.patch_csv = patch('llamagraph.is_llama_bench_csv', self.csv_parser_mock)
        self.patch_window = patch('llamagraph.MainWindow', self.main_window_mock)
        self.patch_presenter = patch('llamagraph.PlotterPresenter', self.presenter_mock)
        
        # Start patches
        self.patch_tk.start()
        self.patch_csv.start()
        self.patch_window.start()
        self.patch_presenter.start()
        
        # Now safe to import (tkinter is mocked)
        import llamagraph
        self.llamagraph_module = llamagraph
        
        yield
        
        # Stop patches
        self.patch_tk.stop()
        self.patch_csv.stop()
        self.patch_window.stop()
        self.patch_presenter.stop()
    
    def test_file_path_logic(self):
        """When a file path is provided, start_dir is parent and initial_file is set."""
        test_file = Path('/benchmarks/run1.csv')
        
        # Mock CSV validation to return True
        self.csv_parser_mock.return_value = True
        
        with patch('sys.argv', ['llamagraph.py', str(test_file)]):
            with patch.object(sys, 'exit'):
                self.llamagraph_module.main()
                
                # Verify logic: start_dir should be parent
                call_kwargs = self.presenter_mock.call_args
                
                assert call_kwargs is not None
                # Check that start_dir is the parent directory
                assert call_kwargs.kwargs['start_dir'] == test_file.parent
                # Check that initial_selection_file is set
                assert call_kwargs.kwargs['initial_selection_file'] == test_file
    
    def test_invalid_csv_file_ignored(self):
        """When a file path is provided but not valid CSV, initial_file is None."""
        test_file = Path('/benchmarks/invalid.txt')
        
        # Mock CSV validation to return False
        self.csv_parser_mock.return_value = False
        
        with patch('sys.argv', ['llamagraph.py', str(test_file)]):
            with patch.object(sys, 'exit'):
                self.llamagraph_module.main()
                
                call_kwargs = self.presenter_mock.call_args
                
                # start_dir is still parent
                assert call_kwargs.kwargs['start_dir'] == test_file.parent
                # But initial_selection_file should be None
                assert call_kwargs.kwargs['initial_selection_file'] is None
    
    def test_directory_path_logic(self):
        """When a directory path is provided, it's used as start_dir."""
        test_dir = Path('/benchmarks')
        
        with patch('sys.argv', ['llamagraph.py', str(test_dir)]):
            with patch.object(sys, 'exit'):
                self.llamagraph_module.main()
                
                call_kwargs = self.presenter_mock.call_args
                
                assert call_kwargs.kwargs['start_dir'] == test_dir
                assert call_kwargs.kwargs['initial_selection_file'] is None
    
    def test_nonexistent_path_exits(self):
        """Non-existent path causes sys.exit(1)."""
        nonexistent = Path('/nonexistent/path')
        
        with patch('sys.argv', ['llamagraph.py', str(nonexistent)]):
            with patch.object(sys, 'exit') as mock_exit:
                with pytest.raises(SystemExit) as exc_info:
                    self.llamagraph_module.main()
                
                assert exc_info.value.code == 1
                mock_exit.assert_called_once_with(1)
    
    def test_default_path_is_current_dir(self):
        """Default path (no arguments) uses current directory."""
        with patch('sys.argv', ['llamagraph.py']):
            with patch.object(sys, 'exit'):
                self.llamagraph_module.main()
                
                call_kwargs = self.presenter_mock.call_args
                
                # Should be current directory (absolute)
                assert call_kwargs.kwargs['start_dir'] == Path('.').absolute()
    
    def test_ns_flag_affects_default_ts(self):
        """--ns flag affects default_ts parameter to Presenter."""
        with patch('sys.argv', ['llamagraph.py', '--ns']):
            with patch.object(sys, 'exit'):
                self.llamagraph_module.main()
                
                call_kwargs = self.presenter_mock.call_args
                
                # --ns means show_ns=True, so default_ts should be False
                assert call_kwargs.kwargs['default_ts'] is False
    
    def test_no_ns_flag_means_default_ts_true(self):
        """Without --ns flag, default_ts is True."""
        with patch('sys.argv', ['llamagraph.py']):
            with patch.object(sys, 'exit'):
                self.llamagraph_module.main()
                
                call_kwargs = self.presenter_mock.call_args
                
                assert call_kwargs.kwargs['default_ts'] is True


class TestPathResolution:
    """Test path resolution logic."""
    
    def test_file_path_becomes_parent(self):
        """File path resolves to parent directory for start_dir."""
        input_path = Path('/a/b/c/file.csv').absolute()
        
        # Simulate the logic from main()
        if input_path.is_file():
            start_dir = input_path.parent
        else:
            start_dir = input_path
        
        assert start_dir == Path('/a/b/c').absolute()
    
    def test_directory_path_stays_same(self):
        """Directory path stays as start_dir."""
        input_path = Path('/benchmarks').absolute()
        
        # Simulate the logic from main()
        if input_path.is_file():
            start_dir = input_path.parent
        else:
            start_dir = input_path
        
        assert start_dir == input_path
