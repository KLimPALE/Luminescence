import ctypes

from pathlib import Path
from typing import Tuple
from typing import List


class Chromator:
    def __init__(self, sdk_path: str = "sdk"):
        self.sdk_path = Path(sdk_path)
        self.library_handle = None
        self.instrument_index = 0
        self.is_initialized = False


    def connect(self) -> bool:
        connection_status = False

        if hasattr(ctypes, 'add_dll_directory'):
            ctypes.add_dll_directory(str(self.sdk_path.absolute()))

        library_path = self.sdk_path / "SolarLS.Sdk.dll"

        if library_path.exists():
            self.library_handle = ctypes.CDLL(str(library_path))

            self.library_handle.sls_Init.argtypes = [ctypes.c_char_p]
            self.library_handle.sls_Init.restype = ctypes.c_int
            self.library_handle.sls_GetInstrumentCount.argtypes = [ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_GetInstrumentCount.restype = ctypes.c_int
            self.library_handle.sls_GetInstrumentName.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
            self.library_handle.sls_GetInstrumentName.restype = ctypes.c_int
            self.library_handle.sls_GetInstrumentSerial.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
            self.library_handle.sls_GetInstrumentSerial.restype = ctypes.c_int
            self.library_handle.sls_GetWl.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
            self.library_handle.sls_GetWl.restype = ctypes.c_int
            self.library_handle.sls_SetWl.argtypes = [ctypes.c_int, ctypes.c_double]
            self.library_handle.sls_SetWl.restype = ctypes.c_int
            self.library_handle.sls_SetWlAsync.argtypes = [ctypes.c_int, ctypes.c_double]
            self.library_handle.sls_SetWlAsync.restype = ctypes.c_int
            self.library_handle.sls_IsValidWl.argtypes = [ctypes.c_int, ctypes.c_double, ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_IsValidWl.restype = ctypes.c_int
            self.library_handle.sls_IsValidWlGrating.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_double, ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_IsValidWlGrating.restype = ctypes.c_int
            self.library_handle.sls_GetSlitCount.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_GetSlitCount.restype = ctypes.c_int
            self.library_handle.sls_GetSlitName.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
            self.library_handle.sls_GetSlitName.restype = ctypes.c_int
            self.library_handle.sls_SetSlitWidth.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_double, ctypes.c_bool]
            self.library_handle.sls_SetSlitWidth.restype = ctypes.c_int
            self.library_handle.sls_SetSlitWidthAsync.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_double, ctypes.c_bool]
            self.library_handle.sls_SetSlitWidthAsync.restype = ctypes.c_int
            self.library_handle.sls_GetSlitWidth.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
            self.library_handle.sls_GetSlitWidth.restype = ctypes.c_int
            self.library_handle.sls_GetMirrorCount.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_GetMirrorCount.restype = ctypes.c_int
            self.library_handle.sls_GetMirrorName.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
            self.library_handle.sls_GetMirrorName.restype = ctypes.c_int
            self.library_handle.sls_GetMirrorStateCount.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_GetMirrorStateCount.restype = ctypes.c_int
            self.library_handle.sls_GetMirrorStateName.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
            self.library_handle.sls_GetMirrorStateName.restype = ctypes.c_int
            self.library_handle.sls_GetMirrorStateIdx.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_GetMirrorStateIdx.restype = ctypes.c_int
            self.library_handle.sls_SetMirrorStateIdx.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
            self.library_handle.sls_SetMirrorStateIdx.restype = ctypes.c_int
            self.library_handle.sls_SetMirrorStateIdxAsync.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
            self.library_handle.sls_SetMirrorStateIdxAsync.restype = ctypes.c_int
            self.library_handle.sls_GetFilterCount.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_GetFilterCount.restype = ctypes.c_int
            self.library_handle.sls_GetFilterName.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
            self.library_handle.sls_GetFilterName.restype = ctypes.c_int
            self.library_handle.sls_GetFilterStateCount.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_GetFilterStateCount.restype = ctypes.c_int
            self.library_handle.sls_GetFilterStateName.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
            self.library_handle.sls_GetFilterStateName.restype = ctypes.c_int
            self.library_handle.sls_GetFilterStatePrm.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_GetFilterStatePrm.restype = ctypes.c_int
            self.library_handle.sls_GetFilterStateIdx.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_GetFilterStateIdx.restype = ctypes.c_int
            self.library_handle.sls_SetFilterStateIdx.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
            self.library_handle.sls_SetFilterStateIdx.restype = ctypes.c_int
            self.library_handle.sls_SetFilterStateIdxAsync.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
            self.library_handle.sls_SetFilterStateIdxAsync.restype = ctypes.c_int
            self.library_handle.sls_GetShutterCount.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_GetShutterCount.restype = ctypes.c_int
            self.library_handle.sls_GetShutterName.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
            self.library_handle.sls_GetShutterName.restype = ctypes.c_int
            self.library_handle.sls_ShutterOpen.argtypes = [ctypes.c_int, ctypes.c_int]
            self.library_handle.sls_ShutterOpen.restype = ctypes.c_int
            self.library_handle.sls_ShutterOpenAsync.argtypes = [ctypes.c_int, ctypes.c_int]
            self.library_handle.sls_ShutterOpenAsync.restype = ctypes.c_int
            self.library_handle.sls_ShutterClose.argtypes = [ctypes.c_int, ctypes.c_int]
            self.library_handle.sls_ShutterClose.restype = ctypes.c_int
            self.library_handle.sls_ShutterCloseAsync.argtypes = [ctypes.c_int, ctypes.c_int]
            self.library_handle.sls_ShutterCloseAsync.restype = ctypes.c_int
            self.library_handle.sls_GetShutterState.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_GetShutterState.restype = ctypes.c_int
            self.library_handle.sls_GetGratingCount.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_GetGratingCount.restype = ctypes.c_int
            self.library_handle.sls_GetActiveGrating.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_GetActiveGrating.restype = ctypes.c_int
            self.library_handle.sls_SetActiveGrating.argtypes = [ctypes.c_int, ctypes.c_int]
            self.library_handle.sls_SetActiveGrating.restype = ctypes.c_int
            self.library_handle.sls_SetActiveGratingAsync.argtypes = [ctypes.c_int, ctypes.c_int]
            self.library_handle.sls_SetActiveGratingAsync.restype = ctypes.c_int
            self.library_handle.sls_GetGratingPrm.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
            self.library_handle.sls_GetGratingPrm.restype = ctypes.c_int
            self.library_handle.sls_GetPixelClbr.argtypes = [ctypes.c_int, ctypes.c_double, ctypes.c_int, ctypes.c_double, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
            self.library_handle.sls_GetPixelClbr.restype = ctypes.c_int
            self.library_handle.sls_GetCalibration.argtypes = [ctypes.c_int, ctypes.c_double, ctypes.c_int, ctypes.c_double, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
            self.library_handle.sls_GetCalibration.restype = ctypes.c_int
            self.library_handle.sls_GetDispersion.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
            self.library_handle.sls_GetDispersion.restype = ctypes.c_int
            self.library_handle.sls_ResetGrating.argtypes = [ctypes.c_int]
            self.library_handle.sls_ResetGrating.restype = ctypes.c_int
            self.library_handle.sls_ResetGratingAsync.argtypes = [ctypes.c_int]
            self.library_handle.sls_ResetGratingAsync.restype = ctypes.c_int
            self.library_handle.sls_ResetSetGrating.argtypes = [ctypes.c_int, ctypes.c_double]
            self.library_handle.sls_ResetSetGrating.restype = ctypes.c_int
            self.library_handle.sls_GetInstrumentStatus.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
            self.library_handle.sls_GetInstrumentStatus.restype = ctypes.c_int
            self.library_handle.sls_GetLastErrorText.argtypes = [ctypes.c_char_p, ctypes.c_int]
            self.library_handle.sls_GetLastErrorText.restype = None

            configuration_path = str(self.sdk_path).encode('utf-8')
            initialization_result = self.library_handle.sls_Init(configuration_path)

            if initialization_result:
                instrument_count = ctypes.c_int()
                self.library_handle.sls_GetInstrumentCount(ctypes.byref(instrument_count))

                if instrument_count.value > 0:
                    self.is_initialized = True
                    connection_status = True

        return connection_status


    def disconnect(self) -> None:
        if self.is_initialized:
            self.is_initialized = False
            self.library_handle = None


    def get_last_error(self) -> str:
        error_message = ""

        if self.is_initialized:
            error_buffer = ctypes.create_string_buffer(512)
            self.library_handle.sls_GetLastErrorText(error_buffer, 512)
            error_message = error_buffer.value.decode('utf-8', errors='ignore')

        return error_message


    def get_instrument_name(self) -> str:
        instrument_name = ""

        if self.is_initialized:
            name_buffer = ctypes.create_string_buffer(256)
            self.library_handle.sls_GetInstrumentName(self.instrument_index, name_buffer, 256)
            instrument_name = name_buffer.value.decode('utf-8', errors='ignore')

        return instrument_name


    def get_instrument_serial(self) -> str:
        serial_number = ""

        if self.is_initialized:
            serial_buffer = ctypes.create_string_buffer(256)
            self.library_handle.sls_GetInstrumentSerial(self.instrument_index, serial_buffer, 256)
            serial_number = serial_buffer.value.decode('utf-8', errors='ignore')

        return serial_number


    def set_wavelength(self, wavelength_nanometers: float) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_SetWl(self.instrument_index, ctypes.c_double(wavelength_nanometers))
            operation_status = bool(result)

        return operation_status


    def set_wavelength_async(self, wavelength_nanometers: float) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_SetWlAsync(self.instrument_index, ctypes.c_double(wavelength_nanometers))
            operation_status = bool(result)

        return operation_status


    def get_wavelength(self) -> float:
        wavelength_value = 0.0

        if self.is_initialized:
            wavelength = ctypes.c_double()
            self.library_handle.sls_GetWl(self.instrument_index, ctypes.byref(wavelength))
            wavelength_value = wavelength.value

        return wavelength_value


    def is_valid_wavelength(self, wavelength_nanometers: float) -> bool:
        validity_status = False

        if self.is_initialized:
            is_valid = ctypes.c_int()
            self.library_handle.sls_IsValidWl(self.instrument_index, ctypes.c_double(wavelength_nanometers), ctypes.byref(is_valid))
            validity_status = bool(is_valid.value)

        return validity_status


    def is_valid_wavelength_for_grating(self, grating_index: int, wavelength_nanometers: float) -> bool:
        validity_status = False

        if self.is_initialized:
            is_valid = ctypes.c_int()
            self.library_handle.sls_IsValidWlGrating(self.instrument_index, grating_index, ctypes.c_double(wavelength_nanometers), ctypes.byref(is_valid))
            validity_status = bool(is_valid.value)

        return validity_status


    def get_status(self) -> int:
        status_value = -1

        if self.is_initialized:
            instrument_status = ctypes.c_int()
            self.library_handle.sls_GetInstrumentStatus(self.instrument_index, ctypes.byref(instrument_status))
            status_value = instrument_status.value

        return status_value


    def is_ready(self) -> bool:
        ready_status = False

        if self.is_initialized:
            status_value = self.get_status()
            ready_status = status_value == 1

        return ready_status


    def get_grating_count(self) -> int:
        grating_count_value = 0

        if self.is_initialized:
            grating_count = ctypes.c_int()
            self.library_handle.sls_GetGratingCount(self.instrument_index, ctypes.byref(grating_count))
            grating_count_value = grating_count.value

        return grating_count_value


    def get_active_grating(self) -> int:
        active_grating_value = -1

        if self.is_initialized:
            active_grating = ctypes.c_int()
            self.library_handle.sls_GetActiveGrating(self.instrument_index, ctypes.byref(active_grating))
            active_grating_value = active_grating.value

        return active_grating_value


    def set_active_grating(self, grating_index: int) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_SetActiveGrating(self.instrument_index, grating_index)
            operation_status = bool(result)

        return operation_status


    def set_active_grating_async(self, grating_index: int) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_SetActiveGratingAsync(self.instrument_index, grating_index)
            operation_status = bool(result)

        return operation_status


    def get_grating_parameters(self, grating_index: int) -> Tuple[int, float, float, float]:
        grooves_value = 0
        minimum_wavelength = 0.0
        maximum_wavelength = 0.0
        blaze_angle_value = 0.0

        if self.is_initialized:
            grooves = ctypes.c_int()
            minimum_wavelength_parameter = ctypes.c_double()
            maximum_wavelength_parameter = ctypes.c_double()
            blaze_angle = ctypes.c_double()
            self.library_handle.sls_GetGratingPrm(
                self.instrument_index,
                grating_index,
                ctypes.byref(grooves),
                ctypes.byref(minimum_wavelength_parameter),
                ctypes.byref(maximum_wavelength_parameter),
                ctypes.byref(blaze_angle)
            )
            grooves_value = grooves.value
            minimum_wavelength = minimum_wavelength_parameter.value
            maximum_wavelength = maximum_wavelength_parameter.value
            blaze_angle_value = blaze_angle.value

        return grooves_value, minimum_wavelength, maximum_wavelength, blaze_angle_value


    def reset_grating(self) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_ResetGrating(self.instrument_index)
            operation_status = bool(result)

        return operation_status


    def reset_grating_async(self) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_ResetGratingAsync(self.instrument_index)
            operation_status = bool(result)

        return operation_status


    def reset_and_set_wavelength(self, wavelength_nanometers: float) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_ResetSetGrating(self.instrument_index, ctypes.c_double(wavelength_nanometers))
            operation_status = bool(result)

        return operation_status


    def get_dispersion(self) -> float:
        dispersion_value = 0.0

        if self.is_initialized:
            dispersion = ctypes.c_double()
            self.library_handle.sls_GetDispersion(self.instrument_index, ctypes.byref(dispersion))
            dispersion_value = dispersion.value

        return dispersion_value


    def get_slit_count(self) -> int:
        slit_count_value = 0

        if self.is_initialized:
            slit_count = ctypes.c_int()
            self.library_handle.sls_GetSlitCount(self.instrument_index, ctypes.byref(slit_count))
            slit_count_value = slit_count.value

        return slit_count_value


    def get_slit_name(self, slit_index: int) -> str:
        slit_name = ""

        if self.is_initialized:
            name_buffer = ctypes.create_string_buffer(256)
            self.library_handle.sls_GetSlitName(self.instrument_index, slit_index, name_buffer, 256)
            slit_name = name_buffer.value.decode('utf-8', errors='ignore')

        return slit_name


    def set_slit_width(self, slit_index: int, width_micrometers: float, reset_required: bool = False) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_SetSlitWidth(self.instrument_index, slit_index, ctypes.c_double(width_micrometers), reset_required)
            operation_status = bool(result)

        return operation_status


    def set_slit_width_async(self, slit_index: int, width_micrometers: float, reset_required: bool = False) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_SetSlitWidthAsync(self.instrument_index, slit_index, ctypes.c_double(width_micrometers), reset_required)
            operation_status = bool(result)

        return operation_status


    def get_slit_width(self, slit_index: int) -> float:
        slit_width_value = 0.0

        if self.is_initialized:
            slit_width = ctypes.c_double()
            self.library_handle.sls_GetSlitWidth(self.instrument_index, slit_index, ctypes.byref(slit_width))
            slit_width_value = slit_width.value

        return slit_width_value


    def get_mirror_count(self) -> int:
        mirror_count_value = 0

        if self.is_initialized:
            mirror_count = ctypes.c_int()
            self.library_handle.sls_GetMirrorCount(self.instrument_index, ctypes.byref(mirror_count))
            mirror_count_value = mirror_count.value

        return mirror_count_value


    def get_mirror_name(self, mirror_index: int) -> str:
        mirror_name = ""

        if self.is_initialized:
            name_buffer = ctypes.create_string_buffer(256)
            self.library_handle.sls_GetMirrorName(self.instrument_index, mirror_index, name_buffer, 256)
            mirror_name = name_buffer.value.decode('utf-8', errors='ignore')

        return mirror_name


    def get_mirror_state_count(self, mirror_index: int) -> int:
        state_count_value = 0

        if self.is_initialized:
            state_count = ctypes.c_int()
            self.library_handle.sls_GetMirrorStateCount(self.instrument_index, mirror_index, ctypes.byref(state_count))
            state_count_value = state_count.value

        return state_count_value


    def get_mirror_state_name(self, mirror_index: int, state_index: int) -> str:
        state_name = ""

        if self.is_initialized:
            name_buffer = ctypes.create_string_buffer(256)
            self.library_handle.sls_GetMirrorStateName(self.instrument_index, mirror_index, state_index, name_buffer, 256)
            state_name = name_buffer.value.decode('utf-8', errors='ignore')

        return state_name


    def get_mirror_state(self, mirror_index: int) -> int:
        state_value = -1

        if self.is_initialized:
            state_index = ctypes.c_int()
            self.library_handle.sls_GetMirrorStateIdx(self.instrument_index, mirror_index, ctypes.byref(state_index))
            state_value = state_index.value

        return state_value


    def set_mirror_state(self, mirror_index: int, state_index: int) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_SetMirrorStateIdx(self.instrument_index, mirror_index, state_index)
            operation_status = bool(result)

        return operation_status


    def set_mirror_state_async(self, mirror_index: int, state_index: int) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_SetMirrorStateIdxAsync(self.instrument_index, mirror_index, state_index)
            operation_status = bool(result)

        return operation_status


    def get_filter_count(self) -> int:
        filter_count_value = 0

        if self.is_initialized:
            filter_count = ctypes.c_int()
            self.library_handle.sls_GetFilterCount(self.instrument_index, ctypes.byref(filter_count))
            filter_count_value = filter_count.value

        return filter_count_value


    def get_filter_name(self, filter_index: int) -> str:
        filter_name = ""

        if self.is_initialized:
            name_buffer = ctypes.create_string_buffer(256)
            self.library_handle.sls_GetFilterName(self.instrument_index, filter_index, name_buffer, 256)
            filter_name = name_buffer.value.decode('utf-8', errors='ignore')

        return filter_name


    def get_filter_state_count(self, filter_index: int) -> int:
        state_count_value = 0

        if self.is_initialized:
            state_count = ctypes.c_int()
            self.library_handle.sls_GetFilterStateCount(self.instrument_index, filter_index, ctypes.byref(state_count))
            state_count_value = state_count.value

        return state_count_value


    def get_filter_state_name(self, filter_index: int, state_index: int) -> str:
        state_name = ""

        if self.is_initialized:
            name_buffer = ctypes.create_string_buffer(256)
            self.library_handle.sls_GetFilterStateName(self.instrument_index, filter_index, state_index, name_buffer, 256)
            state_name = name_buffer.value.decode('utf-8', errors='ignore')

        return state_name


    def get_filter_bandwidth(self, filter_index: int, state_index: int) -> Tuple[int, int]:
        minimum_wavelength = 0
        maximum_wavelength = 0

        if self.is_initialized:
            minimum_wavelength_parameter = ctypes.c_int()
            maximum_wavelength_parameter = ctypes.c_int()
            self.library_handle.sls_GetFilterStatePrm(
                self.instrument_index,
                filter_index,
                state_index,
                ctypes.byref(minimum_wavelength_parameter),
                ctypes.byref(maximum_wavelength_parameter)
            )
            minimum_wavelength = minimum_wavelength_parameter.value
            maximum_wavelength = maximum_wavelength_parameter.value

        return minimum_wavelength, maximum_wavelength


    def get_filter_state(self, filter_index: int) -> int:
        state_value = -1

        if self.is_initialized:
            state_index = ctypes.c_int()
            self.library_handle.sls_GetFilterStateIdx(self.instrument_index, filter_index, ctypes.byref(state_index))
            state_value = state_index.value

        return state_value


    def set_filter_state(self, filter_index: int, state_index: int) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_SetFilterStateIdx(self.instrument_index, filter_index, state_index)
            operation_status = bool(result)

        return operation_status


    def set_filter_state_async(self, filter_index: int, state_index: int) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_SetFilterStateIdxAsync(self.instrument_index, filter_index, state_index)
            operation_status = bool(result)

        return operation_status


    def get_shutter_count(self) -> int:
        shutter_count_value = 0

        if self.is_initialized:
            shutter_count = ctypes.c_int()
            self.library_handle.sls_GetShutterCount(self.instrument_index, ctypes.byref(shutter_count))
            shutter_count_value = shutter_count.value

        return shutter_count_value


    def get_shutter_name(self, shutter_index: int) -> str:
        shutter_name = ""

        if self.is_initialized:
            name_buffer = ctypes.create_string_buffer(256)
            self.library_handle.sls_GetShutterName(self.instrument_index, shutter_index, name_buffer, 256)
            shutter_name = name_buffer.value.decode('utf-8', errors='ignore')

        return shutter_name


    def shutter_open(self, shutter_index: int = 0) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_ShutterOpen(self.instrument_index, shutter_index)
            operation_status = bool(result)

        return operation_status


    def shutter_open_async(self, shutter_index: int = 0) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_ShutterOpenAsync(self.instrument_index, shutter_index)
            operation_status = bool(result)

        return operation_status


    def shutter_close(self, shutter_index: int = 0) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_ShutterClose(self.instrument_index, shutter_index)
            operation_status = bool(result)

        return operation_status


    def shutter_close_async(self, shutter_index: int = 0) -> bool:
        operation_status = False

        if self.is_initialized:
            result = self.library_handle.sls_ShutterCloseAsync(self.instrument_index, shutter_index)
            operation_status = bool(result)

        return operation_status


    def get_shutter_state(self, shutter_index: int = 0) -> int:
        shutter_state_value = -1

        if self.is_initialized:
            shutter_state = ctypes.c_int()
            self.library_handle.sls_GetShutterState(self.instrument_index, shutter_index, ctypes.byref(shutter_state))
            shutter_state_value = shutter_state.value

        return shutter_state_value


    def get_wavelength_at_pixel(self, central_wavelength: float, central_pixel: int, pixel_pitch_micrometers: float, pixel_number: int) -> float:
        wavelength_value = 0.0

        if self.is_initialized:
            wavelength = ctypes.c_double()
            self.library_handle.sls_GetPixelClbr(
                self.instrument_index,
                ctypes.c_double(central_wavelength),
                central_pixel,
                ctypes.c_double(pixel_pitch_micrometers),
                pixel_number,
                ctypes.byref(wavelength)
            )
            wavelength_value = wavelength.value

        return wavelength_value


    def get_calibration_array(self, central_wavelength: float, central_pixel: int, pixel_pitch_micrometers: float, pixel_count: int) -> List[float]:
        calibration_values = []

        if self.is_initialized:
            calibration_array = (ctypes.c_double * pixel_count)()
            self.library_handle.sls_GetCalibration(
                self.instrument_index,
                ctypes.c_double(central_wavelength),
                central_pixel,
                ctypes.c_double(pixel_pitch_micrometers),
                pixel_count,
                calibration_array
            )
            calibration_values = [calibration_array[i] for i in range(pixel_count)]

        return calibration_values
