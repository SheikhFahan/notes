## Singleton

initialize once use always.

code:

```go
import (
    "log"
    "os"
    "sync"
)

type Logger struct {
    // type declarations
    logger *log.Logger // reference the existing logger
}

var (
    // variable declarations
    instance *Logger // create a variable of type *Logger
    once     sync.Once // sync.Once is a type from the "sync" package it's job is to check if the code has already run.
)

func GetInstance() *Logger {
    once.Do(func() {  // if never run then run; otherwise don't run.
        instance = &Logger{
            logger: log.New(os.Stdout, "[LOG] ", log.LstdFlags),
        }
    })

    return instance // for the fist time it will be initialized by the code above then rest of the times; it will just use the global variable "instance"'s value that is why that is declared outside the function.
    // for the same reason once is also decleared outside the function so that it's value is not limited to the function life cycle.
}

func (l *Logger) Info(message string) {
    l.logger.Println(message)
}
```

Usage

```go
log1 := logger.GetInstance()
log2 := logger.GetInstance()
log1.Info("Application started")

println(log1 == log2) // true
```

## Factory

Have a unified way to create a bunch of alike services e.g sendEmailNotification, sendSmsNotification, sendNotification.

  - Create a factory that returns object of the userfull type and the method of that type always do what they are intented to do without any jumbled logic.
  - Each service lives saperate and implements a unified interface.

```
                      Software Services
                           │
          ┌────────────────┴────────────────┐
          │                                 │
     Notification                     Storage
          │                                 │
   ┌──────┴──────┐                 ┌────────┴────────┐
   │             │                 │                 │
 Email        SMS              S3 Storage      Azure Blob
```

A notification factory only deals with the notification branch it knows nothing of the Storage branch

code:

```go
package main

import "fmt"

// NotificationService is the interface both notification types satisfy implicitly.
type NotificationService interface {
	Send(message string) error
}

// EmailNotification implements NotificationService by having a Send method.
type EmailNotification struct{}

func (e EmailNotification) Send(message string) error {
	fmt.Println("Sending email:", message)
	// ... send email
	return nil
}

// SmsNotification also implements NotificationService.
type SmsNotification struct{}

func (s SmsNotification) Send(message string) error {
	fmt.Println("Sending SMS:", message)
	// ... send SMS
	return nil
}

// NewNotification is the factory. Go has no static methods, so this is a
// package-level function instead of a static method on a factory type.
func NewNotification(kind string) (NotificationService, error) {
	switch kind {
	case "email":
		return EmailNotification{}, nil
	case "sms":
		return SmsNotification{}, nil
	default:
		return nil, fmt.Errorf("unknown notification type: %q", kind)
	}
}

func main() {
	svc, err := NewNotification("email")
	if err != nil {
		panic(err)
	}
	svc.Send("Hello, world!")
}
```

```
===================
A real-world analogy is a car manufacturer:

A Factory is like saying:
"Build me an engine."

An Abstract Factory is like saying:
"Build me all the parts for a Toyota."
==================
```

## Abstract Factory

Have a unified way to create a families of realated and dependent objects without specifying their concrete classes.

```
AWS Factory
   ├── AWS Notification
   ├── AWS Storage
   └── AWS Logger

Azure Factory
   ├── Azure Notification
   ├── Azure Storage
   └── Azure Logger
```

```go
package main

import "fmt"

// ---- Products: the family of related interfaces ----

type Notification interface {
	Notify(to, message string) error
}

type Storage interface {
	Save(key string, data []byte) error
}

type Logger interface {
	Log(level, message string)
}

// ---- Abstract Factory: produces the whole family ----

type CloudFactory interface {
	NewNotification() Notification
	NewStorage() Storage
	NewLogger() Logger
}

// ---- Concrete family #1: AWS ----

type awsNotification struct{}
func (awsNotification) Notify(to, message string) error {
	fmt.Printf("[AWS SNS] notify %s: %s\n", to, message)
	return nil
}

type awsStorage struct{}
func (awsStorage) Save(key string, data []byte) error {
	fmt.Printf("[AWS S3] save %q (%d bytes)\n", key, len(data))
	return nil
}

type awsLogger struct{}
func (awsLogger) Log(level, message string) {
	fmt.Printf("[AWS CloudWatch] %s: %s\n", level, message)
}

type AWSFactory struct{}
func (AWSFactory) NewNotification() Notification { return awsNotification{} }
func (AWSFactory) NewStorage() Storage           { return awsStorage{} }
func (AWSFactory) NewLogger() Logger             { return awsLogger{} }

// ---- Concrete family #2: Azure ----

type azureNotification struct{}
func (azureNotification) Notify(to, message string) error {
	fmt.Printf("[Azure Notification Hubs] notify %s: %s\n", to, message)
	return nil
}

type azureStorage struct{}
func (azureStorage) Save(key string, data []byte) error {
	fmt.Printf("[Azure Blob] save %q (%d bytes)\n", key, len(data))
	return nil
}

type azureLogger struct{}
func (azureLogger) Log(level, message string) {
	fmt.Printf("[Azure Monitor] %s: %s\n", level, message)
}

type AzureFactory struct{}
func (AzureFactory) NewNotification() Notification { return azureNotification{} }
func (AzureFactory) NewStorage() Storage           { return azureStorage{} }
func (AzureFactory) NewLogger() Logger             { return azureLogger{} }

// ---- Factory-of-factories: pick the provider ----

func NewCloudFactory(provider string) (CloudFactory, error) {
	switch provider {
	case "aws":
		return AWSFactory{}, nil
	case "azure":
		return AzureFactory{}, nil
	default:
		return nil, fmt.Errorf("unknown provider: %q", provider)
	}
}

// ---- Client code depends only on the abstractions ----

func runApp(f CloudFactory) {
	logger := f.NewLogger()
	storage := f.NewStorage()
	notifier := f.NewNotification()

	logger.Log("INFO", "app starting")
	storage.Save("report.pdf", []byte("...file contents..."))
	notifier.Notify("user@example.com", "your report is ready")
	logger.Log("INFO", "app done")
}

func main() {
	factory, err := NewCloudFactory("aws")
	if err != nil {
		panic(err)
	}
	runApp(factory)
	// Change "aws" to "azure" and the entire stack switches providers,
	// with no change to runApp.
}
```
