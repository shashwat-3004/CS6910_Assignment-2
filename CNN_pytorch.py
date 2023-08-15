# -*- coding: utf-8 -*-
"""Trial

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/18yxYP46kBhiBJ8gJcJQTz2I54UBRWOUV
"""

!pip install wandb

from google.colab import drive
drive.mount('/content/drive')

zip_path = "drive/MyDrive/nature_12K.zip"
!cp "{zip_path}" .
!unzip -q nature_12K.zip
!rm nature_12K.zip

import torch
import torchvision
from torchvision import datasets, transforms
from torch import nn, optim
from torch.nn import functional as F
from torch.utils.data import DataLoader, sampler, random_split
from torchvision import models
import wandb

import os
import glob
import matplotlib.pyplot as plt
import numpy as np

import gc

train_directory=os.path.join("inaturalist_12K","train")
def get_classes(data_dir=train_directory):
    all_data = datasets.ImageFolder(data_dir)
    return all_data.classes

get_classes()

def prepare_datasets(batch_size,directory="inaturalist_12K",data_augmentation=False,test=False):
  train_directory=os.path.join(directory,"train")
  test_directory=os.path.join(directory,"val")
  generator = torch.Generator().manual_seed(42)
  if data_augmentation==True:
    transform = transforms.Compose([
            transforms.RandomHorizontalFlip(p=0.4),
            transforms.RandomVerticalFlip(p=0.3),
            transforms.RandomApply(transforms=[
                transforms.GaussianBlur(kernel_size=(5, 9), sigma=(0.1, 5))
            ], p=0.43),
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ])
    all_train=datasets.ImageFolder(train_directory,transform=transform)
    train_data_len = int(len(all_train)*0.8)
    valid_data_len = int(len(all_train)-(train_data_len))

    train_data,val_data=random_split(all_train,[train_data_len,valid_data_len],generator.manual_seed(42))
    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=False) # shuffle=True?
    val_loader=DataLoader(val_data,batch_size=batch_size,shuffle=False)

    if test==True:
        transform = transforms.Compose([
            transforms.RandomHorizontalFlip(p=0.4),
            transforms.RandomVerticalFlip(p=0.3),
            transforms.RandomApply(transforms=[
                transforms.GaussianBlur(kernel_size=(5, 9), sigma=(0.1, 5))
            ], p=0.43),
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ])
        all_train=datasets.ImageFolder(train_directory,transform=transform)
        train_loader = DataLoader(all_train, batch_size=batch_size, shuffle=False) # shuffle=True?

        test_transform=transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ])
        all_test=datasets.ImageFolder(test_directory,transform=transform)
        test_data_len=len(all_test)
        test_loader=DataLoader(all_test,batch_size=batch_size,shuffle=False)

        return train_loader, test_loader, len(all_train), test_data_len


  else:
    transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ])

    all_train=datasets.ImageFolder(train_directory,transform=transform)
    train_data_len = int(len(all_train)*0.8)
    valid_data_len = int(len(all_train)-(train_data_len))

    train_data,val_data=random_split(all_train,[train_data_len,valid_data_len],generator.manual_seed(42))
    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=False) # shuffle=True?
    val_loader=DataLoader(val_data,batch_size=batch_size,shuffle=False)

    if test==True:
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ])
        all_train=datasets.ImageFolder(train_directory,transform=transform)
        train_loader = DataLoader(all_train, batch_size=batch_size, shuffle=False) # shuffle=True?


        test_transform=transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ])
        all_test=datasets.ImageFolder(test_directory,transform=transform)
        test_data_len=len(all_test)
        test_loader=DataLoader(all_test,batch_size=batch_size,shuffle=False)

        return train_loader, test_loader, len(all_train), test_data_len

  return train_loader,val_loader, train_data_len, valid_data_len

train,val,num_train,num_val=prepare_datasets(256)

#train,test,num_train,num_test=prepare_datasets(256,test=True)

dataiter = iter(test)
images, labels = next(dataiter)
plt.imshow(np.transpose(torchvision.utils.make_grid(
  images[:25], normalize=True, padding=1, nrow=5).numpy(), (1, 2, 0)))
plt.axis('off')

class CNN(nn.Module):
    def __init__(self,activation_function, num_filters,filter_size,
                   dropout, batch_norm, neurons_dense, num_classes=10, image_size=224):
        super(CNN, self).__init__()

        layers=[]
        feature_map_size = image_size

        for i in range(5):
            if i==0:
              layers.append(nn.Conv2d(in_channels=3,out_channels=num_filters[i],kernel_size=filter_size[i]))   # add padding?
            else:
              layers.append(nn.Conv2d(in_channels=num_filters[i-1],out_channels=num_filters[i],kernel_size=filter_size[i]))


            if batch_norm:
              layers.append(nn.BatchNorm2d(num_filters[i]))

            if activation_function == "relu":
              layers.append(nn.ReLU())
            elif activation_function== "gelu":
              layers.append(nn.GELU())
            elif activation_function== "silu":
              layers.append(nn.SiLU())
            elif activation_function== "mish":
              layers.append(nn.Mish())
            elif activation_function== "elu":
              layers.append(nn.ELU())


            #Maxpool

            layers.append(nn.MaxPool2d(kernel_size=2,stride=2))

            feature_map_size = (feature_map_size - filter_size[i] + 1) // 2


          # dense layer activation function chosen  the same as convolution layer activation function for simplicity

        activation_function_dense=activation_function

        if activation_function_dense == "relu":
              activation_dense_layer=nn.ReLU()
        elif activation_function_dense == "gelu":
              activation_dense_layer=nn.GELU()
        elif activation_function_dense == "silu":
              activation_dense_layer=nn.SiLU()
        elif activation_function_dense == "mish":
             activation_dense_layer=nn.Mish()
        elif activation_function_dense == "elu":
              activation_dense_layer=nn.ELU()


        feature_map_size = feature_map_size ** 2 * num_filters[-1]  #Flattening after last conv layer



        self.features = nn.Sequential(*layers)
        self.flatten = nn.Flatten()
        self.dense=nn.Sequential(
            nn.Linear(feature_map_size, neurons_dense), #4, because we want last convolution layer, number of features
            nn.Dropout(dropout),
            activation_dense_layer,
            nn.Linear(neurons_dense, num_classes),
          )


    def forward(self,x):
        x=self.features(x)
        x=self.flatten(x)
        x=self.dense(x)
        return x

model=CNN('relu','relu',num_filters=[16, 16, 16, 16, 16],filter_size=[3,3,3,3,3],batch_norm=False,neurons_dense=1024,dropout=0.3)

af_conv_silu_af_dense_gelu_nf_[64, 64, 64, 64, 64]_fs_[5, 7, 3, 3, 7]_bn_False_bs_128_neurons_1024_dp_0.2_data_aug_False

CNN('silu','gelu',num_filters=[64,64,64,64,64],filter_size=[5,7,3,3,7],batch_norm=False,neurons_dense=1024,dropout=0.2)

print(sum(p.numel() for p in model.parameters() if p.requires_grad))

class EarlyStopper:
    def __init__(self, patience=4, min_delta=0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.min_validation_loss = np.inf

    def early_stop(self, validation_loss):
        if validation_loss < self.min_validation_loss:
            self.min_validation_loss = validation_loss
            self.counter = 0
        elif validation_loss > (self.min_validation_loss + self.min_delta):
            self.counter += 1
            if self.counter >= self.patience:
                return True
        return False

def model_train(activation_function,num_filters,filter_size,
                batch_norm,batch_size,neurons_dense,dropout,data_augmentation):



  cnn_model=CNN(activation_function=activation_function,num_filters=num_filters,filter_size=filter_size,
                batch_norm=batch_norm,neurons_dense=neurons_dense,dropout=dropout)

  device = 'cuda' if torch.cuda.is_available() else 'cpu'
  model = cnn_model.to(device)

  criterion = nn.CrossEntropyLoss()
  optimizer = optim.Adam(model.parameters(), lr=0.0001)
  train,val,num_train,num_val=prepare_datasets(batch_size,data_augmentation=data_augmentation,test=True)

  train_loss_list=[]
  val_loss_list=[]

  for epoch in range(15):  # epoch

    train_loss=0
    total_train_correct=0

    model.train()
    for images, labels in train:

        #Extracting images and target labels for the batch being iterated
        images = images.to(device)
        labels = labels.to(device)

        #Calculating the model output and the cross entropy loss
        train_outputs = model(images)
        train_pred=torch.argmax(train_outputs,dim=1)
        correct_train_pred=sum(train_pred==labels).item()
        total_train_correct+=correct_train_pred
        loss = criterion(train_outputs, labels)

        #Updating weights according to calculated loss
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        train_loss += loss.item()*images.size(0)

    del images
    del labels


    train_accuracy=total_train_correct/len(train.sampler)

    train_loss = train_loss/len(train.sampler)
    train_loss_list.append(train_loss)

    print('Epoch: {} \tTraining Loss: {:.6f}'.format(
        epoch+1, train_loss))


  model_name="best_model_A.pt"
  path=F"/content/gdrive/My Drive/{model_name}"

  torch.save(model.state_dict(),path)

def wandb_sweep():
      # Default values for hyper-parameters
    config_defaults = {
        'activation_function':'relu',
        'num_filters': [64,64,64,64,64],
        'filter_size': [3,3,3,3,3],
        'batch_norm': True,
        'batch_size': 32,
        'neurons_dense':256,
        'dropout': 0.2,
        'data_augmentation': True
    }

    # Initialize a new wandb run
    wandb.init(config=config_defaults)

    # Config saves hyperparameters and inputs
    config = wandb.config

    activation_function=config.activation_function
    num_filters=config.num_filters
    filter_size=config.filter_size
    batch_norm=config.batch_norm
    batch_size=config.batch_size
    neurons_dense=config.neurons_dense
    dropout=config.dropout
    data_augmentation=config.data_augmentation

    es = EarlyStopper()

    # Display the hyperparameters
    run_name = f"af_{activation_function}_nf_{num_filters}_fs_{filter_size}_bn_{batch_norm}_bs_{batch_size}_neurons_{neurons_dense}_dp_{dropout}_data_aug_{data_augmentation}"
    print(run_name)


    cnn_model=CNN(activation_function,num_filters=num_filters,filter_size=filter_size,
                batch_norm=batch_norm,neurons_dense=neurons_dense,dropout=dropout)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = cnn_model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.0001)

    train,val,num_train,num_val=prepare_datasets(batch_size,data_augmentation=data_augmentation)


    train_loss_list=[]
    val_loss_list=[]

    for epoch in range(20):  # epoch set to 20

      train_loss=0
      val_loss=0
      total_train_correct=0
      total_val_correct=0

      model.train()
      for images, labels in train:

        #Extracting images and target labels for the batch being iterated
        images = images.to(device)
        labels = labels.to(device)

        #Calculating the model output and the cross entropy loss
        #train_outputs = model(images)
        #train_pred=torch.argmax(train_outputs,dim=1)
        #correct_train_pred=sum(train_pred==labels).item()
        #total_train_correct+=correct_train_pred
        #loss = criterion(train_outputs, labels)

        #Updating weights according to calculated loss
        optimizer.zero_grad()
        with torch.cuda.amp.autocast():
          train_outputs = model(images)
          loss = criterion(train_outputs, labels)

        loss.backward()
        optimizer.step()
        train_pred=torch.argmax(train_outputs,dim=1)
        correct_train_pred=sum(train_pred==labels).item()
        total_train_correct+=correct_train_pred
        train_loss += loss.item()*images.size(0)

      model.eval()
      for images,labels in val:

        images = images.to(device)
        labels = labels.to(device)

        val_output= model(images)

        loss= criterion(val_output,labels)
        val_pred=torch.argmax(val_output,dim=1)
        correct_val_pred=sum(val_pred==labels).item()
        total_val_correct+=correct_val_pred

        val_loss += loss.item() * images.size(0)

      train_accuracy=total_train_correct/len(train.sampler)
      val_accuracy=total_val_correct/len(val.sampler)

      train_loss = train_loss/len(train.sampler)
      val_loss = val_loss/len(val.sampler)
      train_loss_list.append(train_loss)
      val_loss_list.append(val_loss)

      wandb.log({"training_acc": train_accuracy, "validation_accuracy": val_accuracy, "training_loss": train_loss, "validation loss": val_loss, "Epoch": epoch+1})

      print('Epoch: {} \tTraining Loss: {:.6f} \tValidation Loss: {:.6f} \tTraining Accuracy: {:.6f} \tValidation Accuracy: {:.6f}'.format(
        epoch+1, train_loss, val_loss, train_accuracy, val_accuracy))

      if es.early_stop(val_loss):
        break



    wandb.run.name = run_name
    wandb.run.save()
    wandb.run.finish()

    del model
    del criterion
    del optimizer
    del train_loss_list
    del val_loss_list
    del train
    del val
    del train_accuracy
    del val_accuracy
    torch.cuda.empty_cache()
    gc.collect()

    #plt.plot(train_loss_list, label='Training loss')
    #plt.plot(val_loss_list, label='Validation loss')
    #plt.xlabel("Epochs")
    #plt.ylabel("Loss")
    #plt.legend(frameon=False)

import gc

sweep_config = {
  "name": "Assignment2(Part-A)",
  "method": "bayes",
  "metric": {
      "name":"validation_accuracy",
      "goal": "maximize"
  },
  "early_terminate": {
        "type":"hyperband",
        "min_iter": 5,
        "s": 2
  },
  "parameters": {
        "activation_function": {
            "values": ['relu','gelu','silu','mish','elu']
        },
        "num_filters": {
            "values": [[64,64,64,64,64],[32, 64, 128, 256, 512],[512,256,128,64,32],[128,256,32,64,512]]
        },
        "filter_size": {
            "values": [[3,3,3,3,3],[7,5,3,3,3],[3,3,3,5,7],[5,7,3,3,7]]
        },
        "batch_norm": {
            "values": [True,False]
        },
        "batch_size": {
            "values": [16,32]
        },
        "neurons_dense": {
            "values": [256,512,768]
        },
        "dropout":{
            "values": [0,0.1,0.2]
        },
        "data_augmentation":{
            "values": [True,False]
        }
    }
}

sweep_id = wandb.sweep(sweep_config,  entity="shashwat_mm19b053", project="Assignment-2")
wandb.agent("ai2etv7d",project='Assignment-2', function=wandb_sweep, count=30)

torch.cuda.empty_cache()

!nvidia-smi

