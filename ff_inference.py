from facefusionlib import swapper # Для замены лиц с помощью Face Fusion
from facefusionlib.swapper import DeviceProvider # Для работы с CPU/GPU


# Функция для замены лица
def face_fusion_swap(input_path, target_path, output_path):
	face_fusion_swapper = swapper.swap_face(
			source_paths=[input_path],
			target_path=target_path,
			output_path=output_path,
			provider=DeviceProvider.CPU,
			detector_score=0.65,
			mask_blur=0.7,
			skip_nsfw=True,
			landmarker_score=0.5
		)
	print(f'Результат сохранен в {face_fusion_swapper}')
	return face_fusion_swapper