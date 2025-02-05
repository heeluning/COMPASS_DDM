if __name__ == '__main__':
# Load necessary packages
    import ssms
    import lanfactory 
    import os
    import numpy as np
    from copy import deepcopy
    import torch
    import pandas as pd
    import matplotlib.pyplot as plt
    #%%
    # MAKE CONFIGS

    # Initialize the generator config (for MLP LANs)
    # generator_config = deepcopy(ssms.config.data_generator_config['lan']['mlp'])
    generator_config = deepcopy(ssms.config.data_generator_config['lan'])

    # Specify generative model (one from the list of included models mentioned above)
    generator_config['dgp_list'] = 'angle' 
    # Specify number of parameter sets to simulate
    generator_config['n_parameter_sets'] = 100 
    # Specify how many samples a simulation run should entail
    generator_config['n_samples'] = 1000
    # Specify folder in which to save generated data
    generator_config['output_folder'] = 'data/lan_mlp/'

    # Make model config dict
    model_config = ssms.config.model_config['angle']
    #%%
    # MAKE DATA

    my_dataset_generator = ssms.dataset_generators.data_generator(generator_config = generator_config,
                                                                model_config = model_config)

    training_data = my_dataset_generator.generate_data_training_uniform(save = True)
    #%%
    # MAKE DATALOADERS

    # List of datafiles (here only one)
    folder_ = 'data/lan_mlp/traindata_angle/'
    file_list_ = [folder_ + file_ for file_ in os.listdir(folder_)]

    # Training dataset
    torch_training_dataset = lanfactory.trainers.DatasetTorch(file_ids = file_list_,
                                                            batch_size = 128)

    torch_training_dataloader = torch.utils.data.DataLoader(torch_training_dataset,
                                                            shuffle = True,
                                                            batch_size = None,
                                                            num_workers = 1,
                                                            pin_memory = True)

    # Validation dataset
    torch_validation_dataset = lanfactory.trainers.DatasetTorch(file_ids = file_list_,
                                                            batch_size = 128)

    torch_validation_dataloader = torch.utils.data.DataLoader(torch_validation_dataset,
                                                            shuffle = True,
                                                            batch_size = None,
                                                            num_workers = 1,
                                                            pin_memory = True)
    #%%
    network_config = lanfactory.config.network_configs.network_config_mlp

    print('Network config: ')
    print(network_config)

    train_config = lanfactory.config.network_configs.train_config_mlp

    print('Train config: ')
    print(train_config)
    #%%
    # LOAD NETWORK
    net = lanfactory.trainers.TorchMLP(network_config = deepcopy(network_config),
                                    input_shape = torch_training_dataset.input_dim)
    #                                   save_folder = '/data/torch_models/',
    #                                   generative_model_id = 'angle')
    #%%
    # SAVE CONFIGS
    lanfactory.utils.save_configs(model_id ='angle_torch_',
                                save_folder = 'data/torch_models/angle/', 
                                network_config = network_config, 
                                train_config = train_config, 
                                allow_abs_path_folder_generation = True)
    #%%
    # TRAIN MODEL
    model_trainer=lanfactory.trainers.ModelTrainerTorchMLP(train_config=train_config,
                                            train_dl=torch_training_dataloader,
                                            valid_dl=torch_validation_dataloader,
                                            model=net)
    model_trainer.train_and_evaluate(save_history = True,
                            save_model = True,
                            output_folder= 'data/torch_models/angle',
                            verbose = 0)
    #%%
    network_path_list = os.listdir('data/torch_models/angle')
    network_file_path = ['data/torch_models/angle/' + file_ for file_ in network_path_list if 'state_dict' in file_][0]

    network = lanfactory.trainers.LoadTorchMLPInfer(model_file_path = network_file_path,
                                                    network_config = network_config,
                                                    input_dim = torch_training_dataset.input_dim)

    #%%
    # Two ways to call the network
    # Direct call --> need tensor input
    direct_out = network(torch.from_numpy(np.array([1, 1.5, 0.5, 1.0, 0.1, 0.65, 1], dtype  = np.float32)))
    print('direct call out: ', direct_out)

    # predict_on_batch method
    predict_on_batch_out = network.predict_on_batch(np.array([1, 1.5, 0.5, 1.0, 0.1, 0.65, 1], dtype  = np.float32))
    print('predict_on_batch out: ', predict_on_batch_out)
    #%%
    # show likeliood
    data = pd.DataFrame(np.zeros((2000, 7), 
                        dtype = np.float32), 
                        columns = ['v', 'a', 'z', 't', 'theta', 'rt', 'choice'])
    data['v'] = 0.5
    data['a'] = 0.75
    data['z'] = 0.5
    data['t'] = 0.2
    data['theta'] = 0.1
    data['rt'].iloc[:1000] = np.linspace(5, 0, 1000)
    data['rt'].iloc[1000:] = np.linspace(0, 5, 1000)
    data['choice'].iloc[:1000] = -1
    data['choice'].iloc[1000:] = 1
    print(data['choice'])
    #%%
    # Network predictions
    predict_on_batch_out = network.predict_on_batch(data.values.astype(np.float32))

    # Simulations
    from ssms.basic_simulators import simulator
    sim_out = simulator(model = 'angle', 
                        theta = data.values[0, :-2],
                        n_samples = 2000)
    #%%

    # Plot network predictions
    plt.plot(data['rt'] * data['choice'], np.exp(predict_on_batch_out), color = 'black', label = 'network')
    #%%
    # Plot simulations
    plt.hist(sim_out['rts'] * sim_out['choices'], bins = 30, histtype = 'step', label = 'simulations', color = 'blue', density  = True)
    plt.legend()
    plt.title('SSM likelihood')
    plt.xlabel('rt')
    plt.ylabel('likelihod')
